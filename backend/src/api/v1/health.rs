use axum::{
    extract::State,
    routing::get,
    Json, Router,
};
use sqlx::PgPool;
use crate::config::Settings;
use crate::db::check_db_health;
use crate::error::AppResult;

#[derive(serde::Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    pub environment: String,
    pub database: String,
}

pub fn router() -> Router {
    Router::new()
        .route("/health", get(health_check))
}

async fn health_check(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
) -> AppResult<Json<HealthResponse>> {
    let db_connected = check_db_health(&pool).await;
    Ok(Json(HealthResponse {
        status: if db_connected { "ok" } else { "degraded" }.to_string(),
        service: settings.project_name,
        environment: settings.environment,
        database: if db_connected { "connected" } else { "disconnected" }.to_string(),
    }))
}