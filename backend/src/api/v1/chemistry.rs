use axum::{
    extract::{State, Json},
    routing::post,
    Router,
};
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::models::chemistry::{MolecularPropertiesResponse, Mol3DResponse, SMILESRequest};
use crate::services::ChemistryEngine;

pub fn router() -> Router {
    Router::new()
        .route("/properties", post(get_molecular_properties))
        .route("/3d", post(generate_3d_coordinates))
}

async fn get_molecular_properties(
    State(settings): State<Settings>,
    Json(payload): Json<SMILESRequest>,
) -> AppResult<Json<MolecularPropertiesResponse>> {
    let chemistry_engine = ChemistryEngine::new();
    let result = chemistry_engine.parse_molecular_properties(payload)?;
    Ok(Json(result))
}

async fn generate_3d_coordinates(
    State(settings): State<Settings>,
    Json(payload): Json<SMILESRequest>,
) -> AppResult<Json<Mol3DResponse>> {
    let chemistry_engine = ChemistryEngine::new();
    let result = chemistry_engine.generate_3d_coordinates(payload)?;
    Ok(Json(Mol3DResponse {
        smiles: result.smiles,
        atoms: result.atoms,
        coordinates_3d: result.coordinates_3d,
    }))
}