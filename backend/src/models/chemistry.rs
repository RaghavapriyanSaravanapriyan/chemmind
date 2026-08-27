use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SMILESRequest {
    pub smiles: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MolecularPropertiesResponse {
    pub smiles: String,
    pub molecular_weight: f64,
    pub chemical_formula: String,
    pub atom_count: i32,
    pub is_valid_smiles: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Mol3DResponse {
    pub smiles: String,
    pub atoms: Vec<String>,
    pub coordinates_3d: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Molecule3DInternal {
    pub smiles: String,
    pub atoms: Vec<String>,
    pub coordinates_3d: Vec<Vec<f64>>,
}