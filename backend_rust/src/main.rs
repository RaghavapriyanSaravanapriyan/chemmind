use std::sync::Arc;

use chemmind_backend::{
    AppState,
    config::Settings,
    create_app,
    db::create_pool,
    services::{ai_gateway::AIGateway, api_keys::ApiKeyStore},
};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

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
        api_keys: ApiKeyStore::new(),
    };

    let app = create_app(app_state);

    let port: u16 = std::env::var("PORT")
        .or_else(|_| std::env::var("CHEMMIND_PORT"))
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(8000);
    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], port));
    tracing::info!("Server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}