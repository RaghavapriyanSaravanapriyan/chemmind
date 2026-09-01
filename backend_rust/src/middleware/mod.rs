use axum::{
    extract::{FromRequestParts, Request, State},
    http::{HeaderMap, request::Parts},
    middleware::Next,
    response::Response,
};
use async_trait::async_trait;
use std::sync::Arc;
use uuid::Uuid;
use crate::auth::decode_access_token;
use crate::config::Settings;
use crate::db::PgPool;
use crate::error::AppError;
use crate::models::user::User;

#[derive(Clone)]
pub struct AuthUser(pub User);

impl AuthUser {
    pub fn id(&self) -> Uuid {
        self.0.id
    }
}

#[async_trait]
impl<S: Send + Sync> FromRequestParts<S> for AuthUser {
    type Rejection = AppError;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        parts
            .extensions
            .get::<AuthUser>()
            .cloned()
            .ok_or_else(|| AppError::Auth("Not authenticated".to_string()))
    }
}

pub async fn auth_middleware(
    State(pool): State<PgPool>,
    State(settings): State<Arc<Settings>>,
    headers: HeaderMap,
    mut request: Request,
    next: Next,
) -> Result<Response, AppError> {
    let auth_header = headers
        .get("authorization")
        .and_then(|h| h.to_str().ok())
        .ok_or_else(|| AppError::Auth("Missing authorization header".to_string()))?;

    if !auth_header.starts_with("Bearer ") {
        return Err(AppError::Auth("Invalid authorization header format".to_string()));
    }

    let token = &auth_header[7..];
    let token_data = decode_access_token(token, &settings)?;
    let claims = token_data.claims;

    let user_id = Uuid::parse_str(&claims.sub)
        .map_err(|_| AppError::Auth("Invalid user ID in token".to_string()))?;

    let user = sqlx::query_as!(
        User,
        r#"SELECT id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at FROM users WHERE id = $1"#,
        user_id
    )
    .fetch_optional(&pool)
    .await?
    .ok_or_else(|| AppError::Auth("User not found".to_string()))?;

    if !user.is_active {
        return Err(AppError::Auth("Inactive user".to_string()));
    }

    request.extensions_mut().insert(AuthUser(user));
    Ok(next.run(request).await)
}

pub async fn optional_auth_middleware(
    State(pool): State<PgPool>,
    State(settings): State<Arc<Settings>>,
    headers: HeaderMap,
    mut request: Request,
    next: Next,
) -> Result<Response, AppError> {
    if let Some(auth_header) = headers.get("authorization").and_then(|h| h.to_str().ok()) {
        if auth_header.starts_with("Bearer ") {
            let token = &auth_header[7..];
            if let Ok(token_data) = decode_access_token(token, &settings) {
                let claims = token_data.claims;
                if let Ok(user_id) = Uuid::parse_str(&claims.sub) {
                    if let Ok(Some(user)) = sqlx::query_as!(
                        User,
                        r#"SELECT id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at FROM users WHERE id = $1"#,
                        user_id
                    )
                    .fetch_optional(&pool)
                    .await {
                        if user.is_active {
                            request.extensions_mut().insert(AuthUser(user));
                        }
                    }
                }
            }
        }
    }
    Ok(next.run(request).await)
}