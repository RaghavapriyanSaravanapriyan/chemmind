use axum::{
    extract::State,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::auth::{create_access_token, hash_password, verify_password};
use crate::config::Settings;
use crate::db::PgPool;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::user::{CreateUser, User, UserResponse};

#[derive(Deserialize)]
pub struct LoginRequest {
    pub email: String,
    pub password: String,
}

#[derive(Serialize)]
pub struct TokenResponse {
    pub access_token: String,
    pub token_type: String,
}

pub fn router() -> Router {
    Router::new()
        .route("/register", post(register_user))
        .route("/login", post(login))
        .route("/me", get(get_me))
}

async fn register_user(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    Json(payload): Json<CreateUser>,
) -> AppResult<Json<UserResponse>> {
    // Check if user exists
    let existing = sqlx::query_as!(
        User,
        r#"SELECT id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at FROM users WHERE email = $1"#,
        payload.email
    )
    .fetch_optional(&pool)
    .await?;

    if existing.is_some() {
        return Err(AppError::Conflict("A user with this email already exists".to_string()));
    }

    let hashed = hash_password(&payload.password)?;

    let user = sqlx::query_as!(
        User,
        r#"
        INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser)
        VALUES ($1, $2, $3, TRUE, FALSE)
        RETURNING id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at
        "#,
        payload.email,
        hashed,
        payload.full_name
    )
    .fetch_one(&pool)
    .await?;

    Ok(Json(user.into()))
}

async fn login(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    Json(payload): Json<LoginRequest>,
) -> AppResult<Json<TokenResponse>> {
    let user = sqlx::query_as!(
        User,
        r#"SELECT id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at FROM users WHERE email = $1"#,
        payload.email
    )
    .fetch_optional(&pool)
    .await?
    .ok_or_else(|| AppError::Auth("Incorrect email or password".to_string()))?;

    if !verify_password(&payload.password, &user.hashed_password)? {
        return Err(AppError::Auth("Incorrect email or password".to_string()));
    }

    if !user.is_active {
        return Err(AppError::Auth("Inactive user account".to_string()));
    }

    let access_token = create_access_token(user.id, &settings)?;
    Ok(Json(TokenResponse {
        access_token,
        token_type: "bearer".to_string(),
    }))
}

async fn get_me(
    auth_user: AuthUser,
) -> AppResult<Json<UserResponse>> {
    Ok(Json(auth_user.0.into()))
}