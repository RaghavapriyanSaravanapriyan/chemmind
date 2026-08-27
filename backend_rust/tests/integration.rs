use axum::{
    body::Body,
    http::{Request, StatusCode},
    Router,
};
use serde_json::json;
use sqlx::PgPool;
use tower::ServiceExt;
use uuid::Uuid;

async fn create_test_app(pool: PgPool) -> Router {
    use chemmind_backend::{create_pool, AppState, Settings, services::ai_gateway::AIGateway};
    use std::sync::Arc;

    let settings = Arc::new(Settings {
        database_url: std::env::var("TEST_DATABASE_URL").unwrap_or_else(|_| "postgresql://postgres:postgres@localhost:5432/chemmind_test".to_string()),
        secret_key: "test_secret_key_for_testing_only_32bytes_minimum_length".to_string(),
        ..Default::default()
    });

    let ai_gateway = AIGateway::new(&settings);
    
    let state = AppState {
        pool,
        settings,
        ai_gateway,
    };

    chemmind_backend::create_app(state)
}

#[sqlx::test(migrations = "../migrations")]
async fn test_health_endpoint(pool: PgPool) {
    let app = create_test_app(pool).await;
    
    let response = app
        .oneshot(Request::builder().uri("/health").body(Body::empty()).unwrap())
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::OK);
}

#[sqlx::test(migrations = "../migrations")]
async fn test_user_registration_and_login(pool: PgPool) {
    let app = create_test_app(pool).await;
    
    // Register
    let register_body = json!({
        "email": "test@example.com",
        "password": "securepassword123",
        "full_name": "Test User"
    });
    
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/auth/register")
                .header("content-type", "application/json")
                .body(Body::from(register_body.to_string()))
                .unwrap()
        )
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::CREATED);
    
    // Login
    let login_body = json!({
        "email": "test@example.com",
        "password": "securepassword123"
    });
    
    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/auth/login")
                .header("content-type", "application/json")
                .body(Body::from(login_body.to_string()))
                .unwrap()
        )
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::OK);
}

#[sqlx::test(migrations = "../migrations")]
async fn test_workspace_crud(pool: PgPool) {
    let app = create_test_app(pool).await;
    
    // First register and login to get token
    let register_body = json!({
        "email": "workspace_test@example.com",
        "password": "password123"
    });
    
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/auth/register")
                .header("content-type", "application/json")
                .body(Body::from(register_body.to_string()))
                .unwrap()
        )
        .await
        .unwrap();
    
    let login_body = json!({
        "email": "workspace_test@example.com",
        "password": "password123"
    });
    
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/auth/login")
                .header("content-type", "application/json")
                .body(Body::from(login_body.to_string()))
                .unwrap()
        )
        .await
        .unwrap();
    
    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let token_response: serde_json::Value = serde_json::from_slice(&body).unwrap();
    let token = token_response["access_token"].as_str().unwrap();
    
    // Create workspace
    let create_body = json!({
        "name": "Test Workspace",
        "description": "A test workspace"
    });
    
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/workspaces")
                .header("content-type", "application/json")
                .header("authorization", format!("Bearer {}", token))
                .body(Body::from(create_body.to_string()))
                .unwrap()
        )
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::CREATED);
    
    let body = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let workspace: serde_json::Value = serde_json::from_slice(&body).unwrap();
    let workspace_id = workspace["id"].as_str().unwrap();
    
    // List workspaces
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/api/v1/workspaces")
                .header("authorization", format!("Bearer {}", token))
                .body(Body::empty())
                .unwrap()
        )
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::OK);
    
    // Get workspace
    let response = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri(format!("/api/v1/workspaces/{}", workspace_id))
                .header("authorization", format!("Bearer {}", token))
                .body(Body::empty())
                .unwrap()
        )
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::OK);
}