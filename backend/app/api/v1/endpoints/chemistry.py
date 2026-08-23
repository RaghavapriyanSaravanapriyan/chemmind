from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.ai_gateway import ai_gateway

router = APIRouter()


class SMILESRequest(BaseModel):
    smiles: str = Field(..., description="Chemical SMILES string or compound prompt (e.g. C6H6, methane, C1=CC=CC=C1)")


class MolecularPropertiesResponse(BaseModel):
    smiles: str
    molecular_weight: float
    chemical_formula: str
    atom_count: int
    is_valid_smiles: bool


class Mol3DResponse(BaseModel):
    smiles: str
    atoms: list[str]
    coordinates_3d: list[list[float]]


@router.post(
    "/properties",
    response_model=MolecularPropertiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Molecular Properties from SMILES or prompt",
)
async def get_molecular_properties(request: SMILESRequest) -> Any:
    if not ai_gateway.chemistry_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chemistry engine not available",
        )

    # Convert common molecule prompts to standard SMILES if simple text
    smiles_val = request.smiles.strip()
    if smiles_val.lower() in ["methane", "ch4"]:
        smiles_val = "C"
    elif smiles_val.lower() in ["water", "h2o"]:
        smiles_val = "O"
    elif smiles_val.lower() in ["benzene"]:
        smiles_val = "c1ccccc1"
    elif smiles_val.lower() in ["ethanol"]:
        smiles_val = "CCO"

    props = ai_gateway.chemistry_engine.parse_molecular_properties(smiles_val)
    return MolecularPropertiesResponse(
        smiles=props.smiles,
        molecular_weight=props.molecular_weight,
        chemical_formula=props.chemical_formula,
        atom_count=props.atom_count,
        is_valid_smiles=props.is_valid_smiles,
    )


@router.post(
    "/3d",
    response_model=Mol3DResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate 3D Molecular Coordinates for Spatial Visualisation",
)
async def generate_3d_coordinates(request: SMILESRequest) -> Any:
    if not ai_gateway.chemistry_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chemistry engine not available",
        )

    smiles_val = request.smiles.strip()
    if smiles_val.lower() in ["methane", "ch4"]:
        smiles_val = "C"
    elif smiles_val.lower() in ["water", "h2o"]:
        smiles_val = "O"
    elif smiles_val.lower() in ["benzene"]:
        smiles_val = "c1ccccc1"

    coords = ai_gateway.chemistry_engine.generate_3d_coordinates(smiles_val)
    return Mol3DResponse(
        smiles=coords.smiles,
        atoms=coords.atoms,
        coordinates_3d=coords.coordinates_3d,
    )
