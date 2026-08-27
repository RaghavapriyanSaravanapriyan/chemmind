mod auth;
mod workspaces;
mod documents;
mod conversations;
mod chat;
mod usage;
mod health;

pub use auth::router as auth_router;
pub use workspaces::router as workspaces_router;
pub use documents::router as documents_router;
pub use conversations::router as conversations_router;
pub use chat::router as chat_router;
pub use usage::router as usage_router;
pub use health::router as health_router;

use axum::Router;

pub fn api_router() -> Router {
    Router::new()
        .merge(auth_router())
        .merge(workspaces_router())
        .merge(documents_router())
        .merge(conversations_router())
        .merge(chat_router())
        .merge(usage_router())
        .merge(health_router())
}