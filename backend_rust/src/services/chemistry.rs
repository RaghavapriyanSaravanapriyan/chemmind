use serde::Serialize;
use std::collections::HashMap;

/// Atomic weights used for molecular-weight calculations.
pub const ATOMIC_WEIGHTS: &[(&str, f64)] = &[
    ("H", 1.008),
    ("He", 4.0026),
    ("Li", 6.94),
    ("B", 10.81),
    ("C", 12.011),
    ("N", 14.007),
    ("O", 15.999),
    ("F", 18.998),
    ("Ne", 20.180),
    ("Na", 22.990),
    ("Mg", 24.305),
    ("Si", 28.085),
    ("P", 30.974),
    ("S", 32.06),
    ("Cl", 35.45),
    ("Ar", 39.948),
    ("K", 39.098),
    ("Ca", 40.078),
    ("Fe", 55.845),
    ("Co", 58.933),
    ("Ni", 58.693),
    ("Cu", 63.546),
    ("Zn", 65.38),
    ("Br", 79.904),
    ("I", 126.904),
];

#[derive(Debug, Clone, Serialize)]
pub struct MolecularProperties {
    pub smiles: String,
    pub molecular_weight: f64,
    pub chemical_formula: String,
    pub atom_count: u32,
    pub is_valid_smiles: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct Mol3DCoordinates {
    pub smiles: String,
    pub atoms: Vec<String>,
    pub coordinates_3d: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ParsedAtom {
    pub symbol: String,
    pub count: u32,
}

fn atomic_weight(symbol: &str) -> Option<f64> {
    ATOMIC_WEIGHTS.iter().find(|(s, _)| *s == symbol).map(|(_, w)| *w)
}

/// Very lightweight SMILES tokenizer that understands organic subset syntax.
/// It is intentionally permissive so that common molecules parse correctly,
/// while clearly invalid input is rejected.
pub fn parse_smiles(smiles: &str) -> Result<Vec<ParsedAtom>, String> {
    let s = smiles.trim();
    if s.is_empty() || !s.is_ascii() {
        return Err("Empty or non-ASCII SMILES".to_string());
    }
    if s.contains('\n') || s.contains(' ') {
        return Err("SMILES contains invalid whitespace".to_string());
    }

    let chars: Vec<char> = s.chars().collect();
    let mut atoms: Vec<ParsedAtom> = Vec::new();
    let mut i = 0usize;
    let mut bracket_depth = 0usize;

    while i < chars.len() {
        let c = chars[i];
        match c {
            '(' | ')' | '[' | ']' | '=' | '#' | '-' | '+' | '\\' | '/' | '.' | ':' | '@' | '%' => {
                match c {
                    '[' => bracket_depth += 1,
                    ']' => {
                        if bracket_depth > 0 {
                            bracket_depth -= 1;
                        }
                    }
                    _ => {}
                }
                i += 1;
            }
            '1'..='9' => i += 1,
            c if c.is_ascii_lowercase() => {
                return Err(format!("Invalid SMILES token: '{}'", c));
            }
            c if c.is_ascii_uppercase() => {
                // Two-letter element symbol
                if i + 1 < chars.len() && chars[i + 1].is_ascii_lowercase() {
                    let sym: String = chars[i..i + 2].iter().collect();
                    if atomic_weight(&sym).is_some() {
                        atoms.push(ParsedAtom { symbol: sym, count: 1 });
                        i += 2;
                        continue;
                    }
                }
                let sym = c.to_string();
                if atomic_weight(&sym).is_none() {
                    return Err(format!("Unknown element: '{}'", c));
                }
                atoms.push(ParsedAtom { symbol: sym, count: 1 });
                i += 1;
            }
            c if c.is_numeric() => i += 1,
            _ => return Err(format!("Invalid SMILES character: '{}'", c)),
        }
    }

    if bracket_depth != 0 {
        return Err("Unbalanced brackets in SMILES".to_string());
    }
    if atoms.is_empty() {
        return Err("SMILES contains no atoms".to_string());
    }

    Ok(atoms)
}

fn formula_from_atoms(atoms: &[ParsedAtom]) -> String {
    let mut counts: HashMap<String, u32> = HashMap::new();
    for atom in atoms {
        *counts.entry(atom.symbol.clone()).or_insert(0) += atom.count;
    }

    // Standard Hill ordering: C first, then H, then the rest alphabetically.
    let mut symbols: Vec<&String> = counts.keys().collect();
    symbols.sort();
    symbols.sort_by_key(|s| match s.as_str() {
        "C" => 0,
        "H" => 1,
        _ => 2,
    });

    let mut formula = String::new();
    for sym in symbols {
        let count = counts[sym];
        formula.push_str(sym);
        if count > 1 {
            formula.push_str(&count.to_string());
        }
    }
    formula
}

pub fn compute_properties(smiles: &str) -> MolecularProperties {
    let atoms = parse_smiles(smiles);
    match atoms {
        Ok(atoms) => {
            let total_atoms: u32 = atoms.iter().map(|a| a.count).sum();
            let molecular_weight: f64 = atoms
                .iter()
                .map(|a| atomic_weight(&a.symbol).unwrap_or(0.0) * a.count as f64)
                .sum();
            let formula = formula_from_atoms(&atoms);
            MolecularProperties {
                smiles: smiles.to_string(),
                molecular_weight: (molecular_weight * 1000.0).round() / 1000.0,
                chemical_formula: formula,
                atom_count: total_atoms,
                is_valid_smiles: true,
            }
        }
        Err(_) => MolecularProperties {
            smiles: smiles.to_string(),
            molecular_weight: 0.0,
            chemical_formula: String::new(),
            atom_count: 0,
            is_valid_smiles: false,
        },
    }
}

/// Generates rough 3D coordinates for a molecule using a deterministic
/// pseudo-layout. This is a lightweight fallback that maps each atom to a
/// position on a spiral/zigzag, suitable for visualisation rather than
/// precise geometric optimisation.
pub fn compute_3d_coordinates(smiles: &str) -> Mol3DCoordinates {
    let atoms = match parse_smiles(smiles) {
        Ok(atoms) => atoms,
        Err(_) => {
            return Mol3DCoordinates {
                smiles: smiles.to_string(),
                atoms: vec![],
                coordinates_3d: vec![],
            }
        }
    };

    let mut atom_symbols: Vec<String> = Vec::new();
    let mut coords: Vec<Vec<f64>> = Vec::new();
    let mut idx = 0usize;
    let bond_length = 1.5f64;
    let angle_step = std::f64::consts::TAU / 6.0;

    for atom in &atoms {
        for _ in 0..atom.count {
            let angle = idx as f64 * angle_step;
            let radius = bond_length * (1.0 + (idx as f64).mul_add(0.15, 1.0).sqrt());
            let x = radius * angle.cos();
            let y = radius * angle.sin();
            let z = (idx as f64) * 0.4 - ((idx as f64) % 2.0) * 0.8;
            coords.push(vec![x, y, z]);
            atom_symbols.push(atom.symbol.clone());
            idx += 1;
        }
    }

    Mol3DCoordinates {
        smiles: smiles.to_string(),
        atoms: atom_symbols,
        coordinates_3d: coords,
    }
}
