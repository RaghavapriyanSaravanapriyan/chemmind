use axum::{
    extract::{Path, State},
    routing::get,
    Json, Router,
};
use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::usage::WorkspaceUsageSummary;
use crate::services::usage::UsageService;

pub fn router() -> Router {
    Router::new()
        .route("/{workspace_id}/usage", get(get_workspace_usage))
}

async fn get_workspace_usage(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    auth_user: AuthUser,
    Path(workspace_id): Path<Uuid>,
) -> AppResult<Json<WorkspaceUsageSummary>> {
    crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    let summary = UsageService::get_workspace_usage_summary(&pool, workspace_id, &settings).await?;
    Ok(Json(summary))
}