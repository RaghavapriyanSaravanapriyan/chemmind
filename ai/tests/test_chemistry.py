import unittest
from ai.chemistry.engine import ChemistryEngine

class TestChemistryEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ChemistryEngine()

    def test_smiles_validation_valid(self):
        smiles_aspirin = "CC(=O)OC1=CC=CC=C1C(=O)O"
        self.assertTrue(self.engine.validate_smiles(smiles_aspirin))

    def test_smiles_validation_invalid(self):
        invalid_smiles = "C1==CC((((O=="
        self.assertFalse(self.engine.validate_smiles(invalid_smiles))

    def test_parse_molecular_properties(self):
        smiles_benzene = "c1ccccc1"
        props = self.engine.parse_molecular_properties(smiles_benzene)

        self.assertTrue(props.is_valid_smiles)
        self.assertGreater(props.molecular_weight, 70.0)
        self.assertEqual(props.atom_count, 6)

    def test_generate_3d_coordinates(self):
        smiles_water = "O"
        coords_obj = self.engine.generate_3d_coordinates(smiles_water)

        self.assertEqual(coords_obj.smiles, smiles_water)
        self.assertTrue(len(coords_obj.coordinates_3d) > 0)
        self.assertEqual(len(coords_obj.coordinates_3d[0]), 3)

if __name__ == "__main__":
    unittest.main()
