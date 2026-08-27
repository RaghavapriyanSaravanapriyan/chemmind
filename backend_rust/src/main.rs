mod config;
mod db;
mod auth;
mod models;
mod services;
mod api;
mod error;
mod middleware;

use axum::{
    middleware,
    routing::get,
    Router,
};
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::config::Settings;
use crate::db::{create_pool, PgPool};
use crate::services::ai_gateway::AIGateway;
use crate::api::v1::api_router;
use crate::api::v1::health::router as health_router;

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    pub settings: Arc<Settings>,
    pub ai_gateway: AIGateway,
}

pub fn create_app(state: AppState) -> Router {
    let settings = state.settings.clone();
    
    let cors = CorsLayer::new()
        .allow_origin(settings.backend_cors_origins.clone().into_iter().map(|o| o.parse().unwrap()).collect::<Vec<_>>())
        .allow_credentials(true)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .route("/health", get(health_check))
        .nest("/api/v1", api_router())
        .layer(middleware::from_fn_with_state(
            state.clone(),
            crate::middleware::auth_middleware,
        ))
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info,chemmind_backend=debug".to_string()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let settings = Arc::new(Settings::new().unwrap_or_default());
    
    let pool = create_pool(&settings).await?;
    tracing::info!("Database connected and migrations applied");

    let ai_gateway = AIGateway::new(&settings);

    let app_state = AppState {
        pool: pool.clone(),
        settings: settings.clone(),
        ai_gateway,
    };

    let app = create_app(app_state);

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], 8000));
    tracing::info!("Server starting on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
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