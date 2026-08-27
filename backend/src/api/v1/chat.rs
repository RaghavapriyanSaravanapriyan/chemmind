use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::sse::{Event, KeepAlive, Sse},
    routing::{get, post},
    Json, Router,
};
use futures::{stream, Stream, StreamExt};
use sqlx::PgPool;
use std::convert::Infallible;
use std::time::Duration;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::conversation::{Citation, CreateCitation, Message};
use crate::models::user::User;
use crate::services::ai_gateway::{AIChatRequest, AIChatResponse, AIChatStreamChunk, AIGateway};
use crate::services::usage::UsageService;

pub fn router() -> Router {
    Router::new()
        .route(
            "/{workspace_id}/conversations/{conversation_id}/chat",
            post(chat_query),
        )
        .route(
            "/{workspace_id}/conversations/{conversation_id}/chat/stream",
            get(chat_stream),
        )
}

async fn get_conversation_with_permission(
    pool: &PgPool,
    workspace_id: Uuid,
    conversation_id: Uuid,
    user_id: Uuid,
) -> AppResult<(sqlx::types::Uuid, String)> {
    let workspace = crate::api::v1::workspaces::get_workspace_with_role(pool, workspace_id, user_id).await?;

    let conversation = sqlx::query!(
        r#"SELECT id FROM conversations WHERE id = $1 AND workspace_id = $2"#,
        conversation_id,
        workspace_id
    )
    .fetch_optional(pool)
    .await?
    .ok_or_else(|| AppError::NotFound("Conversation not found".to_string()))?;

    Ok((conversation.id, workspace.role))
}

async fn chat_query(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    auth_user: AuthUser,
    Path((workspace_id, conversation_id)): Path<(Uuid, Uuid)>,
    Json(payload): Json<AIChatRequest>,
) -> AppResult<Json<AIChatResponse>> {
    let (conversation_id, role) = get_conversation_with_permission(&pool, workspace_id, conversation_id, auth_user.id()).await?;
    
    if !["owner", "editor"].contains(&role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can send chat messages".to_string()));
    }

    // Check AI request quota
    UsageService::check_quota_available(&pool, workspace_id, "ai_requests", 1, &settings).await?;

    // 1. Save user query message
    let user_msg = sqlx::query_as!(
        Message,
        r#"
        INSERT INTO messages (conversation_id, sender, content)
        VALUES ($1, 'user', $2)
        RETURNING id, conversation_id, sender, content, created_at
        "#,
        conversation_id,
        payload.prompt
    )
    .fetch_one(&pool)
    .await?;

    // 2. Call AI Gateway
    let (answer_text, citations_in) = ai_gateway.generate_rag_response(payload).await?;

    // 3. Save assistant message
    let asst_msg = sqlx::query_as!(
        Message,
        r#"
        INSERT INTO messages (conversation_id, sender, content)
        VALUES ($1, 'assistant', $2)
        RETURNING id, conversation_id, sender, content, created_at
        "#,
        conversation_id,
        answer_text
    )
    .fetch_one(&pool)
    .await?;

    // 4. Save citation metadata
    for cit in &citations_in {
        sqlx::query!(
            r#"
            INSERT INTO citations (message_id, document_id, page, chunk_id, section, excerpt)
            VALUES ($1, $2, $3, $4, $5, $6)
            "#,
            asst_msg.id,
            cit.document_id,
            cit.page,
            cit.chunk_id,
            cit.section,
            cit.excerpt
        )
        .execute(&pool)
        .await?;
    }

    // 5. Record usage metric
    UsageService::record_usage(&pool, workspace_id, auth_user.id(), "ai_requests", 1).await?;

    // Load citations for response
    let citations = sqlx::query_as!(
        Citation,
        r#"SELECT id, message_id, document_id, page, chunk_id, section, excerpt, created_at FROM citations WHERE message_id = $1 ORDER BY created_at"#,
        asst_msg.id
    )
    .fetch_all(&pool)
    .await?;

    let citation_responses: Vec<crate::models::conversation::CitationResponse> = citations.into_iter().map(Into::into).collect();

    Ok(Json(AIChatResponse {
        message_id: asst_msg.id,
        sender: "assistant".to_string(),
        content: asst_msg.content,
        citations: citation_responses,
    }))
}

async fn chat_stream(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    auth_user: AuthUser,
    Path((workspace_id, conversation_id)): Path<(Uuid, Uuid)>,
    axum::extract::Query(params): axum::extract::Query<std::collections::HashMap<String, String>>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    // Get query parameters for the chat request
    let prompt = params.get("prompt").cloned().unwrap_or_default();
    let selected_document_ids = params.get("selected_document_ids")
        .map(|s| s.split(',').filter_map(|id| Uuid::parse_str(id).ok()).collect());
    let model_provider = params.get("model_provider").cloned();

    let request = AIChatRequest {
        prompt,
        selected_document_ids,
        model_provider,
    };

    let (conversation_id_inner, role) = match get_conversation_with_permission(&pool, workspace_id, conversation_id, auth_user.id()).await {
        Ok(result) => result,
        Err(e) => {
            let error_event = Event::default().json_data(serde_json::json!({
                "error": e.to_string()
            })).unwrap_or_default();
            return Sse::new(stream::once(async move { Ok(error_event) })).keep_alive(KeepAlive::default());
        }
    };

    if !["owner", "editor"].contains(&role.as_str()) {
        let error_event = Event::default().json_data(serde_json::json!({
            "error": "Only workspace owners or editors can stream chat messages"
        })).unwrap_or_default();
        return Sse::new(stream::once(async move { Ok(error_event) })).keep_alive(KeepAlive::default());
    }

    // Check AI request quota
    if let Err(e) = UsageService::check_quota_available(&pool, workspace_id, "ai_requests", 1, &settings).await {
        let error_event = Event::default().json_data(serde_json::json!({
            "error": e.to_string()
        })).unwrap_or_default();
        return Sse::new(stream::once(async move { Ok(error_event) })).keep_alive(KeepAlive::default());
    }

    // Save user message first
    let user_msg = match sqlx::query_as!(
        Message,
        r#"
        INSERT INTO messages (conversation_id, sender, content)
        VALUES ($1, 'user', $2)
        RETURNING id, conversation_id, sender, content, created_at
        "#,
        conversation_id_inner,
        request.prompt
    )
    .fetch_one(&pool)
    .await {
        Ok(msg) => msg,
        Err(e) => {
            let error_event = Event::default().json_data(serde_json::json!({
                "error": format!("Failed to save user message: {}", e)
            })).unwrap_or_default();
            return Sse::new(stream::once(async move { Ok(error_event) })).keep_alive(KeepAlive::default());
        }
    };

    // Stream from AI Gateway
    let chunks = match ai_gateway.stream_rag_response(request).await {
        Ok(chunks) => chunks,
        Err(e) => {
            let error_event = Event::default().json_data(serde_json::json!({
                "error": format!("AI service error: {}", e)
            })).unwrap_or_default();
            return Sse::new(stream::once(async move { Ok(error_event) })).keep_alive(KeepAlive::default());
        }
    };

    let stream = stream::iter(chunks.into_iter().map(|chunk| {
        let json = serde_json::to_string(&chunk).unwrap_or_default();
        Ok(Event::default().data(json))
    }));

    // We need to persist the complete message after streaming
    // This is a limitation of SSE - we'll persist in background after the stream
    let pool_clone = pool.clone();
    let workspace_id_clone = workspace_id;
    let user_id = auth_user.id();
    let conversation_id_clone = conversation_id_inner;

    // Convert stream to also persist at the end
    let persisting_stream = stream.then(move |event| {
        let pool = pool_clone.clone();
        let workspace_id = workspace_id_clone;
        let user_id = user_id;
        let conversation_id = conversation_id_clone;
        
        async move {
            // Check if this is the final chunk
            if let Ok(data) = event.as_ref().map(|e| e.data.clone()) {
                if let Ok(chunk) = serde_json::from_str::<AIChatStreamChunk>(&data) {
                    if chunk.finish_reason == Some("stop".to_string()) {
                        // Persist in background
                        let full_content = chunk.full_content.unwrap_or_default();
                        let citations = chunk.citations.unwrap_or_default();
                        
                        tokio::spawn(async move {
                            if let Ok(asst_msg) = sqlx::query_as!(
                                Message,
                                r#"
                                INSERT INTO messages (conversation_id, sender, content)
                                VALUES ($1, 'assistant', $2)
                                RETURNING id, conversation_id, sender, content, created_at
                                "#,
                                conversation_id,
                                full_content
                            )
                            .fetch_one(&pool)
                            .await {
                                for cit in citations {
                                    let _ = sqlx::query!(
                                        r#"
                                        INSERT INTO citations (message_id, document_id, page, chunk_id, section, excerpt)
                                        VALUES ($1, $2, $3, $4, $5, $6)
                                        "#,
                                        asst_msg.id,
                                        cit.document_id,
                                        cit.page,
                                        cit.chunk_id,
                                        cit.section,
                                        cit.excerpt
                                    )
                                    .execute(&pool)
                                    .await;
                                }
                                let _ = UsageService::record_usage(&pool, workspace_id, user_id, "ai_requests", 1).await;
                            }
                        });
                    }
                }
            }
            event
        }
    });

    Sse::new(persisting_stream).keep_alive(KeepAlive::new().interval(Duration::from_secs(15)))
}