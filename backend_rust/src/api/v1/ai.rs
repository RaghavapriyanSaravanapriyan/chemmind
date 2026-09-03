use axum::{
    extract::{Path, State},
    routing::{delete, get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::services::ai_gateway::AIGateway;
use crate::services::api_keys::{ApiKeyStore, SUPPORTED_PROVIDERS};

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route("/ai/models", get(list_models))
        .route("/ai/health", get(ai_health))
        .route("/ai/config", get(get_config))
        .route("/ai/providers", get(list_providers))
        .route("/ai/embed", post(embed_texts))
        .route("/ai/api-keys/status", get(api_key_status))
        .route("/ai/api-keys", post(set_api_key))
        .route("/ai/api-keys/:provider", delete(delete_api_key))
}

#[derive(Serialize)]
struct ModelsResponse {
    models: Vec<crate::services::ai_gateway::OllamaModelInfo>,
    default_llm_model: String,
    default_embedding_model: String,
    ollama_base_url: String,
    ollama_reachable: bool,
}

async fn list_models(
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    _auth: AuthUser,
) -> AppResult<Json<ModelsResponse>> {
    let ollama = ai_gateway.ollama();
    let (models, reachable) = match ollama.list_models().await {
        Ok(m) => (m, true),
        Err(e) => {
            tracing::warn!("Ollama /api/tags unreachable: {}", e);
            (Vec::new(), false)
        }
    };
    Ok(Json(ModelsResponse {
        models,
        default_llm_model: settings.default_llm_model,
        default_embedding_model: settings.default_embedding_model,
        ollama_base_url: settings.ollama_base_url,
        ollama_reachable: reachable,
    }))
}

#[derive(Serialize)]
struct HealthResponse {
    ollama_reachable: bool,
    ollama_base_url: String,
    default_llm_model: String,
    default_embedding_model: String,
}

async fn ai_health(
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    _auth: AuthUser,
) -> Json<HealthResponse> {
    Json(HealthResponse {
        ollama_reachable: ai_gateway.ollama().ollama_healthy().await,
        ollama_base_url: settings.ollama_base_url,
        default_llm_model: settings.default_llm_model,
        default_embedding_model: settings.default_embedding_model,
    })
}

#[derive(Serialize)]
struct ConfigResponse {
    ollama_base_url: String,
    default_llm_model: String,
    default_embedding_model: String,
    llm_provider: String,
    embedding_provider: String,
    supported_byok_providers: Vec<String>,
}

async fn get_config(State(settings): State<Settings>, _auth: AuthUser) -> Json<ConfigResponse> {
    Json(ConfigResponse {
        ollama_base_url: settings.ollama_base_url,
        default_llm_model: settings.default_llm_model,
        default_embedding_model: settings.default_embedding_model,
        llm_provider: "ollama".to_string(),
        embedding_provider: "ollama".to_string(),
        supported_byok_providers: SUPPORTED_PROVIDERS.iter().map(|s| s.to_string()).collect(),
    })
}

#[derive(Serialize)]
struct ProvidersResponse {
    active_llm_provider: String,
    active_embedding_provider: String,
    default_llm_model: String,
    default_embedding_model: String,
    ollama_reachable: bool,
    supported_byok_providers: Vec<String>,
}

async fn list_providers(
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    _auth: AuthUser,
) -> Json<ProvidersResponse> {
    Json(ProvidersResponse {
        active_llm_provider: "ollama".to_string(),
        active_embedding_provider: "ollama".to_string(),
        default_llm_model: settings.default_llm_model,
        default_embedding_model: settings.default_embedding_model,
        ollama_reachable: ai_gateway.ollama().ollama_healthy().await,
        supported_byok_providers: SUPPORTED_PROVIDERS.iter().map(|s| s.to_string()).collect(),
    })
}

#[derive(Deserialize)]
struct EmbedRequest {
    texts: Option<Vec<String>>,
    input: Option<Vec<String>>,
    model: Option<String>,
    provider: Option<String>,
}

#[derive(Serialize)]
struct EmbedResponse {
    embeddings: Vec<Vec<f32>>,
    model: String,
    dimension: usize,
    mock_fallback: bool,
}

async fn embed_texts(
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    _auth: AuthUser,
    Json(payload): Json<EmbedRequest>,
) -> AppResult<Json<EmbedResponse>> {
    let texts = payload
        .texts
        .or(payload.input)
        .filter(|v| !v.is_empty())
        .ok_or_else(|| AppError::BadRequest("Provide non-empty 'texts' array".to_string()))?;
    if texts.len() > 128 {
        return Err(AppError::BadRequest("Too many texts (max 128)".to_string()));
    }
    let model = payload
        .model
        .filter(|m| !m.trim().is_empty())
        .unwrap_or(settings.default_embedding_model);
    let (embeddings, mock_fallback) = ai_gateway
        .embed_with_model(texts, payload.provider.as_deref(), Some(&model))
        .await?;
    let dimension = embeddings.first().map(|v| v.len()).unwrap_or(0);
    Ok(Json(EmbedResponse {
        embeddings,
        model,
        dimension,
        mock_fallback,
    }))
}

async fn api_key_status(State(keys): State<ApiKeyStore>, _auth: AuthUser) -> Json<serde_json::Value> {
    Json(serde_json::json!({ "providers": keys.status() }))
}

#[derive(Deserialize)]
struct SetKeyRequest {
    provider: String,
    api_key: String,
}

async fn set_api_key(
    State(keys): State<ApiKeyStore>,
    _auth: AuthUser,
    Json(payload): Json<SetKeyRequest>,
) -> AppResult<Json<serde_json::Value>> {
    keys.set(&payload.provider, &payload.api_key)
        .map_err(AppError::BadRequest)?;
    // Never echo the key back.
    Ok(Json(serde_json::json!({
        "ok": true,
        "provider": payload.provider.trim().to_lowercase(),
        "status": keys.status(),
    })))
}

async fn delete_api_key(
    State(keys): State<ApiKeyStore>,
    _auth: AuthUser,
    Path(provider): Path<String>,
) -> Json<serde_json::Value> {
    let removed = keys.delete(&provider);
    Json(serde_json::json!({ "ok": removed, "provider": provider.trim().to_lowercase() }))
}
