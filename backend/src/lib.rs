pub mod api;
pub mod auth;
pub mod config;
pub mod db;
pub mod error;
pub mod middleware;
pub mod models;
pub mod services;

use axum::{extract::FromRef, Router};
use std::sync::Arc;
use tower_http::{cors::CorsLayer, trace::TraceLayer};

use crate::{config::Settings, db::PgPool, services::ai_gateway::AIGateway};

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    pub settings: Arc<Settings>,
    pub ai_gateway: AIGateway,
}

impl FromRef<AppState> for PgPool {
    fn from_ref(state: &AppState) -> Self { state.pool.clone() }
}

impl FromRef<AppState> for Settings {
    fn from_ref(state: &AppState) -> Self { (*state.settings).clone() }
}

impl FromRef<AppState> for AIGateway {
    fn from_ref(state: &AppState) -> Self { state.ai_gateway.clone() }
}

pub fn create_app(state: AppState) -> Router {
    let cors = CorsLayer::new()
        .allow_origin(
            state.settings.backend_cors_origins.iter()
                .map(|origin| origin.parse().expect("invalid CORS origin"))
                .collect::<Vec<_>>(),
        )
        .allow_credentials(true)
        .allow_methods(tower_http::cors::Any)
        .allow_headers(tower_http::cors::Any);

    Router::new()
        .nest("/api/v1", api::v1::api_router())
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}
