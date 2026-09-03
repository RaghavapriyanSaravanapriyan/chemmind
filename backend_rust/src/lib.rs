pub mod config;
pub mod db;
pub mod auth;
pub mod models;
pub mod services;
pub mod api;
pub mod error;
pub mod middleware;

use axum::{
    extract::{FromRef, State},
    http::header::{
        ACCEPT, AUTHORIZATION, CONTENT_TYPE, HeaderName,
    },
    middleware as axum_middleware,
    routing::get,
    Router,
};
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

use crate::config::Settings;
use crate::db::check_db_health;
use crate::services::ai_gateway::AIGateway;
use crate::api::v1::{api_router, protected_router};

#[derive(Clone)]
pub struct AppState {
    pub pool: crate::db::PgPool,
    pub settings: Arc<Settings>,
    pub ai_gateway: AIGateway,
    pub api_keys: crate::services::api_keys::ApiKeyStore,
}

impl FromRef<AppState> for crate::db::PgPool {
    fn from_ref(state: &AppState) -> Self {
        state.pool.clone()
    }
}

impl FromRef<AppState> for Arc<Settings> {
    fn from_ref(state: &AppState) -> Self {
        state.settings.clone()
    }
}

impl FromRef<AppState> for Settings {
    fn from_ref(state: &AppState) -> Self {
        (*state.settings).clone()
    }
}

impl FromRef<AppState> for AIGateway {
    fn from_ref(state: &AppState) -> Self {
        state.ai_gateway.clone()
    }
}

impl FromRef<AppState> for crate::services::api_keys::ApiKeyStore {
    fn from_ref(state: &AppState) -> Self {
        state.api_keys.clone()
    }
}

/// Builds the fully-wired Axum application. Auth middleware only guards
/// protected endpoints; public routes (health, register, login) remain open so
/// the frontend can bootstrap a session.
pub fn create_app(state: AppState) -> Router {
    let settings = state.settings.clone();

    let mut valid_origins = Vec::new();
    for o in settings.backend_cors_origins.clone() {
        match o.parse() {
            Ok(v) => valid_origins.push(v),
            Err(e) => tracing::warn!("Ignoring invalid CORS origin '{}': {}", o, e),
        }
    }
    if valid_origins.is_empty() {
        tracing::warn!("No valid CORS origins configured; defaulting to http://localhost:3000");
        valid_origins.push("http://localhost:3000".parse().expect("default CORS origin"));
    }
    let cors = CorsLayer::new()
        .allow_origin(valid_origins)
        .allow_credentials(true)
        .allow_methods([
            axum::http::Method::GET,
            axum::http::Method::POST,
            axum::http::Method::PUT,
            axum::http::Method::DELETE,
            axum::http::Method::OPTIONS,
        ])
        .allow_headers([
            CONTENT_TYPE,
            AUTHORIZATION,
            ACCEPT,
            HeaderName::from_static("x-requested-with"),
        ]);

    let protected = protected_router().layer(axum_middleware::from_fn_with_state(
        state.clone(),
        crate::middleware::auth_middleware,
    ));

    let api = api_router().merge(protected);

    Router::new()
        .route("/health", get(health_check))
        .nest("/api/v1", api)
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

async fn health_check(
    State(state): State<AppState>,
) -> axum::Json<crate::api::v1::health::HealthResponse> {
    let db_connected = check_db_health(&state.pool).await;
    axum::Json(crate::api::v1::health::HealthResponse {
        status: if db_connected { "ok" } else { "degraded" }.to_string(),
        service: state.settings.project_name.clone(),
        environment: state.settings.environment.clone(),
        database: if db_connected { "connected" } else { "disconnected" }.to_string(),
    })
}