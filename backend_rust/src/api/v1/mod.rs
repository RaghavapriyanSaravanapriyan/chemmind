mod auth;
mod workspaces;
mod documents;
mod conversations;
mod chat;
mod usage;
pub mod health;
mod chemistry;
mod quizzes;
mod reasoning;
mod ai;

pub use workspaces::router as workspaces_router;
pub use documents::router as documents_router;
pub use conversations::router as conversations_router;
pub use chat::router as chat_router;
pub use usage::router as usage_router;
pub use health::router as health_router;
pub use chemistry::router as chemistry_router;
pub use quizzes::router as quizzes_router;
pub use reasoning::router as reasoning_router;
pub use ai::router as ai_router;

use axum::Router;

/// Public API surface: authentication (register/login) and health checks.
/// These routes must be reachable WITHOUT a bearer token so the app can
/// bootstrap a session.
pub fn public_router() -> Router<crate::AppState> {
    Router::new()
        .merge(health_router())
        .route("/auth/register", axum::routing::post(auth::register_user))
        .route("/auth/login", axum::routing::post(auth::login))
}

/// Protected API surface: everything that requires an authenticated user.
/// All endpoints live under `/workspaces` to match the frontend URL contract.
pub fn protected_router() -> Router<crate::AppState> {
    let workspaces = workspaces_router()
        .merge(documents_router())
        .merge(conversations_router())
        .merge(chat_router())
        .merge(usage_router())
        .merge(quizzes_router())
        .merge(reasoning_router());

    Router::new()
        .route("/auth/me", axum::routing::get(auth::get_me))
        .nest("/workspaces", workspaces)
        .merge(chemistry_router())
        .merge(ai_router())
}

/// Combined v1 router. Public routes are merged here; the protected surface
/// must be merged separately after applying the auth middleware.
pub fn api_router() -> Router<crate::AppState> {
    public_router()
}