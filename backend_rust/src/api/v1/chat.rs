use axum::{
    extract::{Path, State},
    response::sse::{Event, KeepAlive, Sse},
    routing::{get, post},
    Json, Router,
};
use futures::{stream, Stream, StreamExt};
use sqlx::PgPool;
use std::convert::Infallible;
use std::pin::Pin;
use std::time::Duration;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::conversation::{Citation, Message};
use crate::services::ai_gateway::{AIChatRequest, AIChatResponse, AIGateway};
use crate::services::usage::UsageService;

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route(
            "/:workspace_id/conversations/:conversation_id/chat",
            post(chat_query),
        )
        .route(
            "/:workspace_id/conversations/:conversation_id/chat/stream",
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
    let _user_msg = sqlx::query_as!(
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

type SseStream = Sse<Pin<Box<dyn Stream<Item = Result<Event, Infallible>> + Send>>>;

async fn chat_stream(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    auth_user: AuthUser,
    Path((workspace_id, conversation_id)): Path<(Uuid, Uuid)>,
    axum::extract::Query(params): axum::extract::Query<std::collections::HashMap<String, String>>,
) -> SseStream {
    let prompt = params.get("prompt").cloned().unwrap_or_default();
    let selected_document_ids = params
        .get("selected_document_ids")
        .map(|s| s.split(',').filter_map(|id| Uuid::parse_str(id).ok()).collect());
    let model_provider = params.get("model_provider").cloned();

    let request = AIChatRequest {
        prompt,
        selected_document_ids,
        model_provider,
    };

    let error_event = |msg: String| {
        let event = Event::default()
            .json_data(serde_json::json!({ "error": msg }))
            .unwrap_or_default();
        Sse::new(Box::pin(stream::once(async move { Ok::<_, Infallible>(event) })) as Pin<Box<dyn Stream<Item = Result<Event, Infallible>> + Send>>)
            .keep_alive(KeepAlive::default())
    };

    let (conversation_id_inner, role) =
        match get_conversation_with_permission(&pool, workspace_id, conversation_id, auth_user.id()).await
        {
            Ok(result) => result,
            Err(e) => return error_event(e.to_string()),
        };

    if !["owner", "editor"].contains(&role.as_str()) {
        return error_event("Only workspace owners or editors can stream chat messages".to_string());
    }

    // Check AI request quota
    if let Err(e) = UsageService::check_quota_available(&pool, workspace_id, "ai_requests", 1, &settings).await {
        return error_event(e.to_string());
    }

    // Save user message first
    if let Err(e) = sqlx::query_as!(
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
    .await
    {
        return error_event(format!("Failed to save user message: {}", e));
    }

    // Stream from AI Gateway
    let chunks = match ai_gateway.stream_rag_response(request).await {
        Ok(chunks) => chunks,
        Err(e) => return error_event(format!("AI service error: {}", e)),
    };

    let pool_clone = pool.clone();
    let workspace_id_clone = workspace_id;
    let user_id = auth_user.id();
    let conversation_id_clone = conversation_id_inner;

    // Emit each chunk as an SSE event; persist the full assistant message +
    // citations from the final chunk's data (axum's Event has no getter).
    let persisting_stream = stream::iter(chunks.into_iter()).then(move |chunk| {
        let pool = pool_clone.clone();
        let workspace_id = workspace_id_clone;
        let user_id = user_id;
        let conversation_id = conversation_id_clone;

        async move {
            let json = serde_json::to_string(&chunk).unwrap_or_default();
            let event = Event::default().data(json);

            if chunk.finish_reason == Some("stop".to_string()) {
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
                    .await
                    {
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

            Ok::<_, Infallible>(event)
        }
    });

    let boxed: Pin<Box<dyn Stream<Item = Result<Event, Infallible>> + Send>> = Box::pin(persisting_stream);
    Sse::new(boxed).keep_alive(KeepAlive::new().interval(Duration::from_secs(15)))
}