use axum::{
    extract::{Path, State},
    routing::{delete, get, post, put},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::workspace::{AddWorkspaceMember, CreateWorkspace, UpdateWorkspace, Workspace, WorkspaceMember, WorkspaceMemberResponse, WorkspaceResponse};

#[derive(Serialize)]
struct WorkspaceWithRole {
    workspace: Workspace,
    role: String,
}

pub(crate) async fn get_workspace_with_role(
    pool: &PgPool,
    workspace_id: Uuid,
    user_id: Uuid,
) -> AppResult<WorkspaceWithRole> {
    let workspace = sqlx::query_as!(
        Workspace,
        r#"SELECT id, name, description, owner_id, is_archived, created_at, updated_at FROM workspaces WHERE id = $1"#,
        workspace_id
    )
    .fetch_optional(pool)
    .await?
    .ok_or_else(|| AppError::NotFound("Workspace not found".to_string()))?;

    if workspace.owner_id == user_id {
        return Ok(WorkspaceWithRole { workspace, role: "owner".to_string() });
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

    Ok(WorkspaceWithRole { workspace, role })
}

pub fn router() -> Router {
    Router::new()
        .route("/", post(create_workspace))
        .route("/", get(list_workspaces))
        .route("/{workspace_id}", get(get_workspace))
        .route("/{workspace_id}", put(update_workspace))
        .route("/{workspace_id}", delete(delete_workspace))
        .route("/{workspace_id}/members", post(add_workspace_member))
}

async fn create_workspace(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    auth_user: AuthUser,
    Json(payload): Json<CreateWorkspace>,
) -> AppResult<Json<WorkspaceResponse>> {
    let workspace = sqlx::query_as!(
        Workspace,
        r#"
        INSERT INTO workspaces (name, description, owner_id, is_archived)
        VALUES ($1, $2, $3, FALSE)
        RETURNING id, name, description, owner_id, is_archived, created_at, updated_at
        "#,
        payload.name,
        payload.description,
        auth_user.id()
    )
    .fetch_one(&pool)
    .await?;

    // Add owner as member
    sqlx::query!(
        r#"INSERT INTO workspace_members (workspace_id, user_id, role) VALUES ($1, $2, 'owner')"#,
        workspace.id,
        auth_user.id()
    )
    .execute(&pool)
    .await?;

    Ok(Json(workspace.into()))
}

async fn list_workspaces(
    State(pool): State<PgPool>,
    auth_user: AuthUser,
) -> AppResult<Json<Vec<WorkspaceResponse>>> {
    let workspaces = sqlx::query_as!(
        Workspace,
        r#"
        SELECT DISTINCT w.id, w.name, w.description, w.owner_id, w.is_archived, w.created_at, w.updated_at
        FROM workspaces w
        LEFT JOIN workspace_members wm ON w.id = wm.workspace_id
        WHERE w.owner_id = $1 OR wm.user_id = $1
        ORDER BY w.updated_at DESC
        "#,
        auth_user.id()
    )
    .fetch_all(&pool)
    .await?;

    Ok(Json(workspaces.into_iter().map(Into::into).collect()))
}

async fn get_workspace(
    State(pool): State<PgPool>,
    Path(workspace_id): Path<Uuid>,
    auth_user: AuthUser,
) -> AppResult<Json<WorkspaceResponse>> {
    let result = get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    Ok(Json(result.workspace.into()))
}

async fn update_workspace(
    State(pool): State<PgPool>,
    Path(workspace_id): Path<Uuid>,
    auth_user: AuthUser,
    Json(payload): Json<UpdateWorkspace>,
) -> AppResult<Json<WorkspaceResponse>> {
    let result = get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    
    if !["owner", "editor"].contains(&result.role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can update workspace details".to_string()));
    }

    let workspace = sqlx::query_as!(
        Workspace,
        r#"
        UPDATE workspaces SET
            name = COALESCE($1, name),
            description = COALESCE($2, description),
            is_archived = COALESCE($3, is_archived),
            updated_at = NOW()
        WHERE id = $4
        RETURNING id, name, description, owner_id, is_archived, created_at, updated_at
        "#,
        payload.name,
        payload.description,
        payload.is_archived,
        workspace_id
    )
    .fetch_one(&pool)
    .await?;

    Ok(Json(workspace.into()))
}

async fn delete_workspace(
    State(pool): State<PgPool>,
    Path(workspace_id): Path<Uuid>,
    auth_user: AuthUser,
) -> AppResult<()> {
    let result = get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    
    if result.role != "owner" {
        return Err(AppError::Forbidden("Only the workspace owner can delete a workspace".to_string()));
    }

    sqlx::query!("DELETE FROM workspaces WHERE id = $1", workspace_id)
        .execute(&pool)
        .await?;

    Ok(())
}

async fn add_workspace_member(
    State(pool): State<PgPool>,
    Path(workspace_id): Path<Uuid>,
    auth_user: AuthUser,
    Json(payload): Json<AddWorkspaceMember>,
) -> AppResult<Json<WorkspaceMemberResponse>> {
    let result = get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    
    if !["owner", "editor"].contains(&result.role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can add members".to_string()));
    }

    // Check if target user exists
    let target_user = sqlx::query_as!(
        crate::models::user::User,
        r#"SELECT id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at FROM users WHERE id = $1"#,
        payload.user_id
    )
    .fetch_optional(&pool)
    .await?;

    if target_user.is_none() {
        return Err(AppError::NotFound("Target user to add not found".to_string()));
    }

    // Check if already member
    let existing = sqlx::query_as!(
        WorkspaceMember,
        r#"SELECT id, workspace_id, user_id, role, created_at FROM workspace_members WHERE workspace_id = $1 AND user_id = $2"#,
        workspace_id,
        payload.user_id
    )
    .fetch_optional(&pool)
    .await?;

    if existing.is_some() {
        return Err(AppError::Conflict("User is already a member of this workspace".to_string()));
    }

    let member = sqlx::query_as!(
        WorkspaceMember,
        r#"
        INSERT INTO workspace_members (workspace_id, user_id, role)
        VALUES ($1, $2, $3)
        RETURNING id, workspace_id, user_id, role, created_at
        "#,
        workspace_id,
        payload.user_id,
        payload.role
    )
    .fetch_one(&pool)
    .await?;

    Ok(Json(member.into()))
}