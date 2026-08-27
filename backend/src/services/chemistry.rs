use std::collections::HashMap;
use crate::error::{AppError, AppResult};
use crate::models::chemistry::{MolecularPropertiesResponse, Molecule3DInternal, SMILESRequest};

pub struct ChemistryEngine;

impl ChemistryEngine {
    pub fn new() -> Self {
        Self
    }

    pub fn parse_molecular_properties(&self, request: SMILESRequest) -> AppResult<MolecularPropertiesResponse> {
        let smiles = request.smiles.trim();
        let normalized_smiles = Self::normalize_smiles(smiles);
        
        let (is_valid, mol_weight, formula, atom_count) = Self::calculate_properties(&normalized_smiles);
        
        Ok(MolecularPropertiesResponse {
            smiles: normalized_smiles,
            molecular_weight: mol_weight,
            chemical_formula: formula,
            atom_count,
            is_valid_smiles: is_valid,
        })
    }

    pub fn generate_3d_coordinates(&self, request: SMILESRequest) -> AppResult<Molecule3DInternal> {
        let smiles = request.smiles.trim();
        let normalized_smiles = Self::normalize_smiles(smiles);
        
        let (atoms, coords) = Self::generate_3d_heuristic(&normalized_smiles);
        
        Ok(Molecule3DInternal {
            smiles: normalized_smiles,
            atoms,
            coordinates_3d: coords,
        })
    }

    fn normalize_smiles(smiles: &str) -> String {
        let lower = smiles.to_lowercase();
        match lower.as_str() {
            "methane" | "ch4" => "C".to_string(),
            "water" | "h2o" => "O".to_string(),
            "benzene" => "c1ccccc1".to_string(),
            "ethanol" => "CCO".to_string(),
            "methanol" => "CO".to_string(),
            "acetone" => "CC(=O)C".to_string(),
            "acetic acid" | "ethanoic acid" => "CC(=O)O".to_string(),
            "glucose" => "C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O".to_string(),
            _ => smiles.to_string(),
        }
    }

    fn calculate_properties(smiles: &str) -> (bool, f64, String, i32) {
        let parser = SmilesParser::new();
        match parser.parse(smiles) {
            Ok(mol) => {
                let mol_weight = mol.molecular_weight();
                let formula = mol.molecular_formula();
                let atom_count = mol.atoms.len() as i32;
                (true, mol_weight, formula, atom_count)
            }
            Err(_) => {
                // Fallback for known molecules
                let fallback = Self::fallback_properties(smiles);
                (false, fallback.0, fallback.1, fallback.2)
            }
        }
    }

    fn fallback_properties(smiles: &str) -> (f64, String, i32) {
        let known: HashMap<&str, (f64, String, i32)> = HashMap::from([
            ("C", (16.04, "CH4".to_string(), 5)),
            ("O", (18.02, "H2O".to_string(), 3)),
            ("c1ccccc1", (78.11, "C6H6".to_string(), 12)),
            ("CCO", (46.07, "C2H6O".to_string(), 9)),
            ("CO", (32.04, "CH4O".to_string(), 6)),
            ("CC(=O)C", (58.08, "C3H6O".to_string(), 10)),
            ("CC(=O)O", (60.05, "C2H4O2".to_string(), 8)),
        ]);
        
        known.get(smiles).copied().unwrap_or((0.0, "Unknown".to_string(), 0))
    }

    fn generate_3d_heuristic(smiles: &str) -> (Vec<String>, Vec<Vec<f64>>) {
        match smiles {
            "C" => Self::methane_3d(),
            "O" => Self::water_3d(),
            "c1ccccc1" => Self::benzene_3d(),
            "CCO" => Self::ethanol_3d(),
            _ => Self::generic_3d(smiles),
        }
    }

    fn methane_3d() -> (Vec<String>, Vec<Vec<f64>>) {
        let atoms = vec!["C".to_string(), "H".to_string(), "H".to_string(), "H".to_string(), "H".to_string()];
        let coords = vec![
            vec![0.0, 0.0, 0.0],
            vec![0.63, 0.63, 0.63],
            vec![-0.63, -0.63, 0.63],
            vec![-0.63, 0.63, -0.63],
            vec![0.63, -0.63, -0.63],
        ];
        (atoms, coords)
    }

    fn water_3d() -> (Vec<String>, Vec<Vec<f64>>) {
        let atoms = vec!["O".to_string(), "H".to_string(), "H".to_string()];
        let coords = vec![
            vec![0.0, 0.0, 0.0],
            vec![0.76, 0.59, 0.0],
            vec![-0.76, 0.59, 0.0],
        ];
        (atoms, coords)
    }

    fn benzene_3d() -> (Vec<String>, Vec<Vec<f64>>) {
        let mut atoms = Vec::new();
        let mut coords = Vec::new();
        let radius = 1.4;
        
        for i in 0..6 {
            atoms.push("C".to_string());
            let angle = (i as f64) * std::f64::consts::PI / 3.0;
            coords.push(vec![
                radius * angle.cos(),
                radius * angle.sin(),
                0.0,
            ]);
        }
        for i in 0..6 {
            atoms.push("H".to_string());
            let angle = (i as f64) * std::f64::consts::PI / 3.0;
            let h_radius = radius + 1.1;
            coords.push(vec![
                h_radius * angle.cos(),
                h_radius * angle.sin(),
                0.0,
            ]);
        }
        (atoms, coords)
    }

    fn ethanol_3d() -> (Vec<String>, Vec<Vec<f64>>) {
        let atoms = vec![
            "C".to_string(), "C".to_string(), "O".to_string(),
            "H".to_string(), "H".to_string(), "H".to_string(),
            "H".to_string(), "H".to_string(), "H".to_string(),
        ];
        let coords = vec![
            vec![0.0, 0.0, 0.0],
            vec![1.54, 0.0, 0.0],
            vec![2.98, 0.0, 0.0],
            vec![-0.51, 0.89, 0.63],
            vec![-0.51, -0.89, 0.63],
            vec![-0.51, 0.0, -1.26],
            vec![2.05, 0.89, -0.63],
            vec![2.05, -0.89, -0.63],
            vec![3.49, 0.0, 0.96],
        ];
        (atoms, coords)
    }

    fn generic_3d(smiles: &str) -> (Vec<String>, Vec<Vec<f64>>) {
        let parser = SmilesParser::new();
        if let Ok(mol) = parser.parse(smiles) {
            let mut atoms = Vec::new();
            let mut coords = Vec::new();
            for (i, atom) in mol.atoms.iter().enumerate() {
                atoms.push(atom.symbol.clone());
                let angle = (i as f64) * 2.0 * std::f64::consts::PI / mol.atoms.len() as f64;
                coords.push(vec![angle.cos(), angle.sin(), 0.0]);
            }
            return (atoms, coords);
        }
        (vec!["X".to_string()], vec![vec![0.0, 0.0, 0.0]])
    }
}

struct SmilesParser;

struct ParsedMolecule {
    atoms: Vec<ParsedAtom>,
    bonds: Vec<(usize, usize, BondType)>,
}

struct ParsedAtom {
    symbol: String,
    implicit_h: u8,
    charge: i8,
}

enum BondType {
    Single,
    Double,
    Triple,
    Aromatic,
}

impl SmilesParser {
    fn new() -> Self {
        Self
    }

    fn parse(&self, smiles: &str) -> Result<ParsedMolecule, String> {
        let mut atoms = Vec::new();
        let mut bonds = Vec::Vec::new();
        let mut bracket_content = String::new();
        let mut in_bracket = false;
        let mut bond_stack: Vec<BondType> = vec![BondType::Single];
        let mut atom_indices: Vec<usize> = Vec::new();
        let mut chars = smiles.chars().peekable();
        
        while let Some(c) = chars.next() {
            match c {
                '[' => {
                    in_bracket = true;
                    bracket_content.clear();
                }
                ']' => {
                    in_bracket = false;
                    let atom = Self::parse_bracket_atom(&bracket_content)?;
                    atoms.push(atom);
                    atom_indices.push(atoms.len() - 1);
                }
                c if c.is_ascii_alphabetic() && !in_bracket => {
                    let mut symbol = c.to_string();
                    if let Some(&next_c) = chars.peek() {
                        if next_c.is_ascii_lowercase() {
                            symbol.push(chars.next().unwrap());
                        }
                    }
                    let atom = ParsedAtom {
                        symbol: symbol.clone(),
                        implicit_h: Self::implicit_hydrogens(&symbol),
                        charge: 0,
                    };
                    atoms.push(atom);
                    atom_indices.push(atoms.len() - 1);
                }
                '=' => bond_stack.push(BondType::Double),
                '#' => bond_stack.push(BondType::Triple),
                ':' => bond_stack.push(BondType::Aromatic),
                '(' => {
                    bond_stack.push(BondType::Single);
                }
                ')' => {
                    bond_stack.pop();
                }
                c if c.is_ascii_digit() => {
                    let ring_num = c.to_digit(10).unwrap() as usize;
                }
                _ => {}
            }
            
            if atom_indices.len() >= 2 && !in_bracket {
                let bond_type = bond_stack.last().cloned().unwrap_or(BondType::Single);
                let idx1 = atom_indices[atom_indices.len() - 2];
                let idx2 = atom_indices[atom_indices.len() - 1];
                bonds.push((idx1, idx2, bond_type));
            }
        }

        Ok(ParsedMolecule { atoms, bonds })
    }

    fn parse_bracket_atom(content: &str) -> Result<ParsedAtom, String> {
        let mut symbol = String::new();
        let mut charge = 0;
        let mut h_count: Option<u8> = None;
        
        for c in content.chars() {
            if c.is_ascii_alphabetic() {
                symbol.push(c);
            } else if c == '+' || c == '-' {
                charge = if c == '+' { 1 } else { -1 };
            } else if c == 'H' {
                h_count = Some(1);
            } else if c.is_ascii_digit() && h_count.is_some() {
                h_count = Some(c.to_digit(10).unwrap() as u8);
            }
        }
        
        Ok(ParsedAtom {
            symbol,
            implicit_h: h_count.unwrap_or(0),
            charge,
        })
    }

    fn implicit_hydrogens(symbol: &str) -> u8 {
        match symbol {
            "C" => 4, "N" => 3, "O" => 2, "F" | "Cl" | "Br" | "I" => 1,
            "S" => 2, "P" => 3, "B" => 3, "Si" => 4,
            _ => 0,
        }
    }
}

impl ParsedMolecule {
    fn molecular_weight(&self) -> f64 {
        let atomic_weights: HashMap<&str, f64> = HashMap::from([
            ("H", 1.008), ("He", 4.003), ("Li", 6.94), ("Be", 9.012), ("B", 10.81),
            ("C", 12.011), ("N", 14.007), ("O", 15.999), ("F", 18.998), ("Ne", 20.180),
            ("Na", 22.990), ("Mg", 24.305), ("Al", 26.982), ("Si", 28.085), ("P", 30.974),
            ("S", 32.06), ("Cl", 35.45), ("Ar", 39.948), ("K", 39.098), ("Ca", 40.078),
            ("Fe", 55.845), ("Cu", 63.546), ("Zn", 65.38), ("Br", 79.904), ("I", 126.904),
        ]);
        
        self.atoms.iter().map(|a| {
            atomic_weights.get(a.symbol.as_str()).unwrap_or(&0.0) 
            + a.implicit_h as f64 * 1.008
        }).sum()
    }

    fn molecular_formula(&self) -> String {
        let mut counts: HashMap<String, u32> = HashMap::new();
        for atom in &self.atoms {
            *counts.entry(atom.symbol.clone()).or_default() += 1 + atom.implicit_h as u32;
        }
        
        let mut elements: Vec<_> = counts.into_iter().collect();
        elements.sort_by_key(|(sym, _)| match sym.as_str() {
            "C" => 0, "H" => 1, _ => 2,
        });
        
        elements.iter().map(|(sym, count)| {
            if *count == 1 { sym.clone() } else { format!("{}{}", sym, count) }
        }).collect()
    }
}