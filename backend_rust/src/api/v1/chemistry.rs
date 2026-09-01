use axum::{extract::State, routing::post, Json, Router};
use serde::Deserialize;
use crate::config::Settings;
use crate::services::chemistry::compute_3d_coordinates;
use crate::services::chemistry::compute_properties;

#[derive(Deserialize)]
pub struct ChemistryRequest {
    pub smiles: Option<String>,
    pub prompt: Option<String>,
}

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route("/chemistry/properties", post(chemistry_properties))
        .route("/chemistry/3d", post(chemistry_3d))
}

async fn chemistry_properties(
    State(_settings): State<Settings>,
    Json(payload): Json<ChemistryRequest>,
) -> Json<crate::services::chemistry::MolecularProperties> {
    let smiles = payload.smiles.or(payload.prompt).unwrap_or_default();
    Json(compute_properties(&smiles))
}

async fn chemistry_3d(
    State(_settings): State<Settings>,
    Json(payload): Json<ChemistryRequest>,
) -> Json<crate::services::chemistry::Mol3DCoordinates> {
    let smiles = payload.smiles.or(payload.prompt).unwrap_or_default();
    Json(compute_3d_coordinates(&smiles))
}
