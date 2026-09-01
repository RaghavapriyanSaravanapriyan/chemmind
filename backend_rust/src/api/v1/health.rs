use axum::{
    extract::State,
    routing::get,
    Json, Router,
};
use serde::Serialize;
use sqlx::PgPool;
use crate::config::Settings;
use crate::db::check_db_health;

#[derive(Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    pub environment: String,
    pub database: String,
}

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route("/health", get(health_check))
}

async fn health_check(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
) -> Json<HealthResponse> {
    let db_connected = check_db_health(&pool).await;
    Json(HealthResponse {
        status: if db_connected { "ok" } else { "degraded" }.to_string(),
        service: settings.project_name,
        environment: settings.environment,
        database: if db_connected { "connected" } else { "disconnected" }.to_string(),
    })
}