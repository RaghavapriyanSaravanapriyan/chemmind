import pytest
from ai.chemistry.engine import ChemistryEngine, ATOMIC_WEIGHTS
from ai.schemas.chemistry import MolecularProperties, Mol3DCoordinates


@pytest.fixture
def chem_engine():
    return ChemistryEngine()


def test_validate_smiles_valid_structures(chem_engine: ChemistryEngine):
    valid_smiles = [
        "C",                      # Methane
        "O",                      # Water
        "CCO",                    # Ethanol
        "c1ccccc1",               # Benzene (aromatic)
        "CC(=O)O",                # Acetic acid
        "C1=CC=CC=C1",            # Benzene (explicit double bonds)
        "CC(C)CC",                # Isopentane (branched)
        "C1CCCCC1",               # Cyclohexane
    ]
    for smi in valid_smiles:
        assert chem_engine.validate_smiles(smi) is True, f"Failed for valid SMILES: {smi}"


def test_validate_smiles_invalid_structures(chem_engine: ChemistryEngine):
    invalid_smiles = [
        "C((C",                   # Unbalanced parentheses
        "C[Na",                   # Unbalanced square brackets
        "C#%*&",                  # Invalid chemical characters
        "",                       # Empty string
        None,                     # None type
        12345,                    # Non-string type
    ]
    for smi in invalid_smiles:
        assert chem_engine.validate_smiles(smi) is False, f"Failed for invalid SMILES: {smi}"


def test_parse_molecular_properties_methane(chem_engine: ChemistryEngine):
    props = chem_engine.parse_molecular_properties("C")
    assert isinstance(props, MolecularProperties)
    assert props.is_valid_smiles is True
    assert props.smiles == "C"
    # Carbon is 12.011 + implicit hydrogens
    assert props.molecular_weight > 12.0
    assert "C" in props.chemical_formula
    assert props.atom_count >= 1


def test_parse_molecular_properties_benzene(chem_engine: ChemistryEngine):
    props = chem_engine.parse_molecular_properties("c1ccccc1")
    assert props.is_valid_smiles is True
    assert props.smiles == "c1ccccc1"
    # Benzene C6H6 is ~78.11 g/mol
    assert 70.0 < props.molecular_weight < 85.0
    assert "C" in props.chemical_formula


def test_parse_molecular_properties_ethanol(chem_engine: ChemistryEngine):
    props = chem_engine.parse_molecular_properties("CCO")
    assert props.is_valid_smiles is True
    assert props.smiles == "CCO"
    # Ethanol C2H6O is ~46.07 g/mol
    assert 40.0 < props.molecular_weight < 55.0
    assert "C" in props.chemical_formula
    assert "O" in props.chemical_formula


def test_parse_molecular_properties_invalid_smiles(chem_engine: ChemistryEngine):
    props = chem_engine.parse_molecular_properties("C(((invalid")
    assert props.is_valid_smiles is False
    assert props.molecular_weight == 0.0
    assert props.chemical_formula == "N/A"
    assert props.atom_count == 0


def test_generate_3d_coordinates_valid_molecule(chem_engine: ChemistryEngine):
    coords = chem_engine.generate_3d_coordinates("CCO")
    assert isinstance(coords, Mol3DCoordinates)
    assert coords.smiles == "CCO"
    assert len(coords.atoms) >= 2
    assert len(coords.coordinates_3d) == len(coords.atoms)
    
    # Check coordinate point structure [x, y, z]
    for pt in coords.coordinates_3d:
        assert len(pt) == 3
        assert all(isinstance(v, (int, float)) for v in pt)


def test_generate_3d_coordinates_invalid_molecule(chem_engine: ChemistryEngine):
    coords = chem_engine.generate_3d_coordinates("invalid(((")
    assert isinstance(coords, Mol3DCoordinates)
    assert coords.atoms == []
    assert coords.coordinates_3d == []


def test_atomic_weights_dictionary_completeness():
    essential_elements = ["H", "C", "N", "O", "F", "P", "S", "Cl", "Br", "I"]
    for elem in essential_elements:
        assert elem in ATOMIC_WEIGHTS
        assert ATOMIC_WEIGHTS[elem] > 0.0
