use axum::{
    extract::{Path, State},
    routing::{delete, get, post},
    Json, Router,
};
use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::conversation::{Conversation, Message, Citation, CreateConversation, CreateMessage, ConversationResponse, MessageResponse, CitationResponse};

async fn get_conversation_with_permission(
    pool: &PgPool,
    workspace_id: Uuid,
    conversation_id: Uuid,
    user_id: Uuid,
) -> AppResult<(Conversation, String)> {
    let workspace = crate::api::v1::workspaces::get_workspace_with_role(pool, workspace_id, user_id).await?;

    let conversation = sqlx::query_as!(
        Conversation,
        r#"SELECT id, workspace_id, user_id, title, created_at, updated_at FROM conversations WHERE id = $1 AND workspace_id = $2"#,
        conversation_id,
        workspace_id
    )
    .fetch_optional(pool)
    .await?
    .ok_or_else(|| AppError::NotFound("Conversation not found".to_string()))?;

    Ok((conversation, workspace.role))
}

pub fn router() -> Router {
    Router::new()
        .route("/{workspace_id}/conversations", post(create_conversation))
        .route("/{workspace_id}/conversations", get(list_conversations))
        .route("/{workspace_id}/conversations/{conversation_id}", get(get_conversation))
        .route("/{workspace_id}/conversations/{conversation_id}/messages", post(add_message))
        .route("/{workspace_id}/conversations/{conversation_id}", delete(delete_conversation))
}

async fn create_conversation(
    State(pool): State<PgPool>,
    Path(workspace_id): Path<Uuid>,
    auth_user: AuthUser,
    Json(payload): Json<CreateConversation>,
) -> AppResult<Json<ConversationResponse>> {
    crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;

    let conversation = sqlx::query_as!(
        Conversation,
        r#"
        INSERT INTO conversations (workspace_id, user_id, title)
        VALUES ($1, $2, $3)
        RETURNING id, workspace_id, user_id, title, created_at, updated_at
        "#,
        workspace_id,
        auth_user.id(),
        payload.title.unwrap_or_else(|| "New Conversation".to_string())
    )
    .fetch_one(&pool)
    .await?;

    Ok(Json(conversation.into()))
}

async fn list_conversations(
    State(pool): State<PgPool>,
    Path(workspace_id): Path<Uuid>,
    auth_user: AuthUser,
) -> AppResult<Json<Vec<ConversationResponse>>> {
    crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;

    let conversations = sqlx::query_as!(
        Conversation,
        r#"SELECT id, workspace_id, user_id, title, created_at, updated_at FROM conversations WHERE workspace_id = $1 ORDER BY updated_at DESC"#,
        workspace_id
    )
    .fetch_all(&pool)
    .await?;

    Ok(Json(conversations.into_iter().map(Into::into).collect()))
}

async fn get_conversation(
    State(pool): State<PgPool>,
    Path((workspace_id, conversation_id)): Path<(Uuid, Uuid)>,
    auth_user: AuthUser,
) -> AppResult<Json<ConversationResponse>> {
    let (conversation, _) = get_conversation_with_permission(&pool, workspace_id, conversation_id, auth_user.id()).await?;

    // Load messages with citations
    let messages = sqlx::query_as!(
        Message,
        r#"SELECT id, conversation_id, sender, content, created_at FROM messages WHERE conversation_id = $1 ORDER BY created_at"#,
        conversation_id
    )
    .fetch_all(&pool)
    .await?;

    let mut conversation_response: ConversationResponse = conversation.into();
    
    for msg in messages {
        let citations = sqlx::query_as!(
            Citation,
            r#"SELECT id, message_id, document_id, page, chunk_id, section, excerpt, created_at FROM citations WHERE message_id = $1 ORDER BY created_at"#,
            msg.id
        )
        .fetch_all(&pool)
        .await?;

        let mut msg_response: MessageResponse = msg.into();
        msg_response.citations = citations.into_iter().map(Into::into).collect();
        conversation_response.messages.push(msg_response);
    }

    Ok(Json(conversation_response))
}

async fn add_message(
    State(pool): State<PgPool>,
    Path((workspace_id, conversation_id)): Path<(Uuid, Uuid)>,
    auth_user: AuthUser,
    Json(payload): Json<CreateMessage>,
) -> AppResult<Json<MessageResponse>> {
    let (conversation, role) = get_conversation_with_permission(&pool, workspace_id, conversation_id, auth_user.id()).await?;
    
    if !["owner", "editor"].contains(&role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can add messages".to_string()));
    }

    // Create Message
    let message = sqlx::query_as!(
        Message,
        r#"
        INSERT INTO messages (conversation_id, sender, content)
        VALUES ($1, $2, $3)
        RETURNING id, conversation_id, sender, content, created_at
        "#,
        conversation.id,
        payload.sender,
        payload.content
    )
    .fetch_one(&pool)
    .await?;

    // Add Citations if provided
    for cit_in in payload.citations {
        sqlx::query!(
            r#"
            INSERT INTO citations (message_id, document_id, page, chunk_id, section, excerpt)
            VALUES ($1, $2, $3, $4, $5, $6)
            "#,
            message.id,
            cit_in.document_id,
            cit_in.page,
            cit_in.chunk_id,
            cit_in.section,
            cit_in.excerpt
        )
        .execute(&pool)
        .await?;
    }

    // Load citations for response
    let citations = sqlx::query_as!(
        Citation,
        r#"SELECT id, message_id, document_id, page, chunk_id, section, excerpt, created_at FROM citations WHERE message_id = $1 ORDER BY created_at"#,
        message.id
    )
    .fetch_all(&pool)
    .await?;

    let mut msg_response: MessageResponse = message.into();
    msg_response.citations = citations.into_iter().map(Into::into).collect();
    
    Ok(Json(msg_response))
}

async fn delete_conversation(
    State(pool): State<PgPool>,
    Path((workspace_id, conversation_id)): Path<(Uuid, Uuid)>,
    auth_user: AuthUser,
) -> AppResult<()> {
    let (conversation, role) = get_conversation_with_permission(&pool, workspace_id, conversation_id, auth_user.id()).await?;
    
    if !["owner", "editor"].contains(&role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can delete conversations".to_string()));
    }

    sqlx::query!("DELETE FROM conversations WHERE id = $1", conversation.id)
        .execute(&pool)
        .await?;

    Ok(())
}