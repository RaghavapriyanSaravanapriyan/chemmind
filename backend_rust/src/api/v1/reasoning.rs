use axum::{
    extract::{Path, State},
    routing::post,
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::AppResult;
use crate::middleware::AuthUser;
use crate::services::ai_gateway::AIGateway;
use crate::services::usage::UsageService;

#[derive(Deserialize)]
pub struct MultiDocRequest {
    pub query_text: Option<String>,
    pub document_ids: Option<Vec<Uuid>>,
    pub model_provider: Option<String>,
}

#[derive(Serialize)]
pub struct MultiDocResponse {
    pub summary: String,
    pub comparison_matrix: Vec<ComparisonRow>,
    pub discrepancies: Vec<Discrepancy>,
    pub citations: Vec<serde_json::Value>,
    pub workspace_id: Uuid,
}

#[derive(Serialize)]
pub struct ComparisonRow {
    pub topic: String,
    pub document_id: String,
    pub excerpt: String,
    pub value_or_finding: String,
}

#[derive(Serialize)]
pub struct Discrepancy {
    pub topic: String,
    pub document_id_a: String,
    pub claim_a: String,
    pub document_id_b: String,
    pub claim_b: String,
    pub nature_of_conflict: String,
}

pub fn router() -> Router<crate::AppState> {
    Router::new().route(
        "/:workspace_id/reasoning/multi-doc",
        post(multi_doc_reasoning),
    )
}

async fn multi_doc_reasoning(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    auth_user: AuthUser,
    Path(workspace_id): Path<Uuid>,
    Json(payload): Json<MultiDocRequest>,
) -> AppResult<Json<MultiDocResponse>> {
    crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;

    UsageService::check_quota_available(&pool, workspace_id, "ai_requests", 1, &settings).await?;
    UsageService::record_usage(&pool, workspace_id, auth_user.id(), "ai_requests", 1).await?;

    let query_text = payload.query_text.unwrap_or_else(|| "Compare document claims".to_string());
    let document_ids = payload.document_ids.unwrap_or_default();

    let grounded_context = if !document_ids.is_empty() {
        crate::services::document_text::build_grounded_context(&pool, &document_ids).await
    } else {
        None
    };

    let value = ai_gateway
        .generate_multi_doc(query_text, document_ids, payload.model_provider, grounded_context)
        .await?;

    let comparison_matrix: Vec<ComparisonRow> = value
        .get("comparison_matrix")
        .and_then(|m| m.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|item| {
                    Some(ComparisonRow {
                        topic: item.get("topic")?.as_str()?.to_string(),
                        document_id: item.get("document_id")?.as_str()?.to_string(),
                        excerpt: item.get("excerpt")?.as_str()?.to_string(),
                        value_or_finding: item.get("value_or_finding")?.as_str()?.to_string(),
                    })
                })
                .collect()
        })
        .unwrap_or_default();

    let discrepancies: Vec<Discrepancy> = value
        .get("discrepancies")
        .and_then(|d| d.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|item| {
                    Some(Discrepancy {
                        topic: item.get("topic")?.as_str()?.to_string(),
                        document_id_a: item.get("document_id_a")?.as_str()?.to_string(),
                        claim_a: item.get("claim_a")?.as_str()?.to_string(),
                        document_id_b: item.get("document_id_b")?.as_str()?.to_string(),
                        claim_b: item.get("claim_b")?.as_str()?.to_string(),
                        nature_of_conflict: item.get("nature_of_conflict")?.as_str()?.to_string(),
                    })
                })
                .collect()
        })
        .unwrap_or_default();

    let summary = value
        .get("summary")
        .and_then(|s| s.as_str())
        .unwrap_or("Synthesis complete.")
        .to_string();

    Ok(Json(MultiDocResponse {
        summary,
        comparison_matrix,
        discrepancies,
        citations: vec![],
        workspace_id,
    }))
}
