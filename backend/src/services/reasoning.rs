use crate::error::{AppError, AppResult};
use crate::models::reasoning::{ComparisonMatrixItem, DiscrepancyItem, MultiDocAnalysisRequestInternal, MultiDocResponse};
use crate::models::conversation::CitationResponse;
use crate::services::ai_gateway::{AIGateway, AIChatRequest};
use uuid::Uuid;

pub struct MultiDocReasoningEngine;

impl MultiDocReasoningEngine {
    pub fn new() -> Self {
        Self
    }

    pub async fn analyze(
        &self,
        ai_gateway: &AIGateway,
        request: MultiDocAnalysisRequestInternal,
    ) -> AppResult<MultiDocResponse> {
        let doc_ids_str = request.document_ids.iter()
            .map(|id| id.to_string())
            .collect::<Vec<_>>()
            .join(", ");

        let prompt = format!(
            r#"You are ChemMind, an AI assistant for chemistry research. Perform a multi-document synthesis on the topic "{query}" across documents: {doc_ids}.

Return ONLY a valid JSON object matching this exact schema:
{{
  "summary": "Overall summary of the analysis...",
  "comparison_matrix": [
    {{"topic": "Topic name", "document_id": "Doc 1", "excerpt": "Relevant excerpt", "value_or_finding": "Key finding"}}
  ],
  "discrepancies": [
    {{"topic": "Topic name", "document_id_a": "Doc 1", "claim_a": "Claim from doc A", "document_id_b": "Doc 2", "claim_b": "Claim from doc B", "nature_of_conflict": "Type of discrepancy"}}
  ]
}}

Focus on:
1. Key findings per document per topic
2. Contradictions or discrepancies between documents
3. Consensus areas
4. Methodological differences"#,
            query = request.query_text,
            doc_ids = doc_ids_str
        );

        let ai_request = AIChatRequest {
            prompt,
            selected_document_ids: Some(request.document_ids),
            model_provider: Some("ollama".to_string()),
        };

        let (response_text, _) = ai_gateway.generate_rag_response(ai_request).await?;
        
        let analysis_data: serde_json::Value = serde_json::from_str(&response_text)
            .map_err(|e| AppError::Internal(format!("Failed to parse multi-doc JSON: {}", e)))?;

        let summary = analysis_data["summary"].as_str()
            .unwrap_or("Multi-document synthesis complete.")
            .to_string();

        let mut comparison_matrix = Vec::new();
        if let Some(matrix) = analysis_data["comparison_matrix"].as_array() {
            for item in matrix {
                comparison_matrix.push(ComparisonMatrixItem {
                    topic: item["topic"].as_str().unwrap_or("").to_string(),
                    document_id: item["document_id"].as_str().unwrap_or("").to_string(),
                    excerpt: item["excerpt"].as_str().unwrap_or("").to_string(),
                    value_or_finding: item["value_or_finding"].as_str().unwrap_or("").to_string(),
                });
            }
        }

        let mut discrepancies = Vec::new();
        if let Some(discs) = analysis_data["discrepancies"].as_array() {
            for item in discs {
                discrepancies.push(DiscrepancyItem {
                    topic: item["topic"].as_str().unwrap_or("").to_string(),
                    document_id_a: item["document_id_a"].as_str().unwrap_or("").to_string(),
                    claim_a: item["claim_a"].as_str().unwrap_or("").to_string(),
                    document_id_b: item["document_id_b"].as_str().unwrap_or("").to_string(),
                    claim_b: item["claim_b"].as_str().unwrap_or("").to_string(),
                    nature_of_conflict: item["nature_of_conflict"].as_str().unwrap_or("").to_string(),
                });
            }
        }

        Ok(MultiDocResponse {
            summary,
            comparison_matrix,
            discrepancies,
            citations: vec![],
            workspace_id: request.workspace_id,
        })
    }
}