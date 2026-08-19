from typing import List, Optional
from pydantic import BaseModel, Field

class MolecularProperties(BaseModel):
    smiles: str = Field(..., description="SMILES string representation of the molecule")
    iupac_name: Optional[str] = Field(default=None, description="IUPAC chemical name if resolved")
    molecular_weight: float = Field(..., description="Molecular weight in g/mol")
    chemical_formula: str = Field(..., description="Standard empirical chemical formula (e.g. C9H8O4)")
    atom_count: int = Field(..., description="Total heavy atom count")
    is_valid_smiles: bool = Field(default=True, description="True if SMILES string is syntactically valid")

class Mol3DCoordinates(BaseModel):
    smiles: str = Field(..., description="Target SMILES string")
    atoms: List[str] = Field(default_factory=list, description="List of atomic element symbols (e.g. ['C', 'C', 'O', 'H'])")
    coordinates_3d: List[List[float]] = Field(default_factory=list, description="List of [x, y, z] spatial coordinates for 3D visualization")
