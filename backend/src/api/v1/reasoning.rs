use axum::{
    extract::{Path, State},
    routing::post,
    Json, Router,
};
use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::reasoning::{MultiDocRequestSchema, MultiDocResponse};
use crate::models::workspace::{Workspace, WorkspaceMember};
use crate::services::{ai_gateway::AIGateway, reasoning::MultiDocReasoningEngine};

pub fn router() -> Router {
    Router::new()
        .route("/{workspace_id}/reasoning/multi-doc", post(analyze_multi_documents))
}

async fn get_workspace_with_role(
    pool: &PgPool,
    workspace_id: Uuid,
    user_id: Uuid,
) -> AppResult<(Workspace, String)> {
    let workspace = sqlx::query_as!(
        Workspace,
        r#"SELECT id, name, description, owner_id, is_archived, created_at, updated_at FROM workspaces WHERE id = $1"#,
        workspace_id
    )
    .fetch_optional(pool)
    .await?
    .ok_or_else(|| AppError::NotFound("Workspace not found".to_string()))?;

    if workspace.owner_id == user_id {
        return Ok((workspace, "owner".to_string()));
    }

    let member = sqlx::query_as!(
        WorkspaceMember,
        r#"SELECT id, workspace_id, user_id, role, created_at FROM workspace_members WHERE workspace_id = $1 AND user_id = $2"#,
        workspace_id,
        user_id
    )
    .fetch_optional(pool)
    .await?;

    let role = member.map(|m| m.role).ok_or_else(|| {
        AppError::Forbidden("You do not have access to this workspace".to_string())
    })?;

    Ok((workspace, role))
}

async fn analyze_multi_documents(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    auth_user: AuthUser,
    Path(workspace_id): Path<Uuid>,
    Json(payload): Json<MultiDocRequestSchema>,
) -> AppResult<Json<MultiDocResponse>> {
    let (_, role) = get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    
    if !["owner", "editor"].contains(&role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can run multi-doc analysis".to_string()));
    }

    let reasoning_engine = MultiDocReasoningEngine::new();
    let request = crate::models::reasoning::MultiDocAnalysisRequestInternal {
        workspace_id,
        query_text: payload.query_text,
        document_ids: payload.document_ids,
    };

    let result = reasoning_engine.analyze(&ai_gateway, request).await?;
    Ok(Json(result))
}