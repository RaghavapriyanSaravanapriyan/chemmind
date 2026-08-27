import re
from typing import List, Optional
from ai.schemas.chemistry import Mol3DCoordinates, MolecularProperties
from ai.utils.logger import logger

# Atomic weights for pure Python fallback calculation
ATOMIC_WEIGHTS = {
    "H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
    "F": 18.998, "P": 30.974, "S": 32.06, "Cl": 35.45, "Br": 79.904, "I": 126.904
}

class ChemistryEngine:
    """
    Deep Chemistry & Molecular Property Engine.
    Provides SMILES validation, empirical formula parsing, molecular weight calculation,
    and 3D molecular coordinate generation.
    """

    def validate_smiles(self, smiles: str) -> bool:
        """Validates SMILES string syntax."""
        if not smiles or not isinstance(smiles, str):
            return False

        # Attempt RDKit validation if available
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(smiles)
            return mol is not None
        except ImportError:
            # Fallback syntax check: check for balanced brackets & valid organic atom symbols
            if re.search(r"[^\w\(\)\=\#\-\+\@\[\]\\\/]", smiles):
                return False
            open_parens = smiles.count("(") - smiles.count(")")
            open_brackets = smiles.count("[") - smiles.count("]")
            return open_parens == 0 and open_brackets == 0

    def parse_molecular_properties(self, smiles: str) -> MolecularProperties:
        """Computes molecular weight, heavy atom count, and chemical formula for a SMILES string."""
        is_valid = self.validate_smiles(smiles)
        
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, rdMolDescriptors
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                mw = Descriptors.MolWt(mol)
                formula = rdMolDescriptors.CalcMolFormula(mol)
                atoms = mol.GetNumAtoms()
                return MolecularProperties(
                    smiles=smiles,
                    molecular_weight=round(mw, 3),
                    chemical_formula=formula,
                    atom_count=atoms,
                    is_valid_smiles=True
                )
        except ImportError:
            pass

        # Pure Python heuristic fallback
        atoms_found = re.findall(r"Br|Cl|[A-Za-z]", smiles)
        atom_count = len(atoms_found)
        
        # Estimate molecular weight from detected atom symbols
        mw = 0.0
        counts = {}
        for raw_elem in atoms_found:
            elem = raw_elem.upper()
            weight = ATOMIC_WEIGHTS.get(elem, 12.011)
            mw += weight
            # Account for implicit hydrogens on aromatic carbons/nitrogens
            if raw_elem.islower() and elem == "C":
                mw += ATOMIC_WEIGHTS["H"]
                counts["H"] = counts.get("H", 0) + 1
            counts[elem] = counts.get(elem, 0) + 1

        # Format empirical formula string (e.g. C6H12O6)
        formula_parts = []
        for elem in ["C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"]:
            if elem in counts:
                cnt = counts.pop(elem)
                formula_parts.append(f"{elem}{cnt if cnt > 1 else ''}")
        for elem, cnt in counts.items():
            formula_parts.append(f"{elem}{cnt if cnt > 1 else ''}")

        formula_str = "".join(formula_parts) or "C"

        return MolecularProperties(
            smiles=smiles,
            molecular_weight=round(mw, 3) if is_valid else 0.0,
            chemical_formula=formula_str if is_valid else "N/A",
            atom_count=atom_count if is_valid else 0,
            is_valid_smiles=is_valid
        )

    def generate_3d_coordinates(self, smiles: str) -> Mol3DCoordinates:
        """Generates 3D molecular spatial coordinates for 3D visualization components."""
        props = self.parse_molecular_properties(smiles)
        
        if not props.is_valid_smiles:
            return Mol3DCoordinates(smiles=smiles, atoms=[], coordinates_3d=[])

        atoms_found = re.findall(r"Br|Cl|[A-Z][a-z]?", smiles) or ["C"]
        coords: List[List[float]] = []

        # Generate estimated 3D mesh grid coordinates
        import math
        for i, atom in enumerate(atoms_found):
            angle = (2 * math.pi * i) / len(atoms_found)
            x = round(1.5 * math.cos(angle), 3)
            y = round(1.5 * math.sin(angle), 3)
            z = round(0.5 * (i % 2), 3)
            coords.append([x, y, z])

        return Mol3DCoordinates(
            smiles=smiles,
            atoms=atoms_found,
            coordinates_3d=coords
        )
