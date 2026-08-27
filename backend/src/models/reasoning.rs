use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::models::conversation::CitationResponse;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComparisonMatrixItem {
    pub topic: String,
    pub document_id: String,
    pub excerpt: String,
    pub value_or_finding: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscrepancyItem {
    pub topic: String,
    pub document_id_a: String,
    pub claim_a: String,
    pub document_id_b: String,
    pub claim_b: String,
    pub nature_of_conflict: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiDocRequestSchema {
    pub query_text: String,
    pub document_ids: Vec<Uuid>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiDocResponse {
    pub summary: String,
    pub comparison_matrix: Vec<ComparisonMatrixItem>,
    pub discrepancies: Vec<DiscrepancyItem>,
    pub citations: Vec<CitationResponse>,
    pub workspace_id: Uuid,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiDocAnalysisRequestInternal {
    pub workspace_id: Uuid,
    pub query_text: String,
    pub document_ids: Vec<Uuid>,
}