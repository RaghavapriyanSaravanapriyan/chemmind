import unittest
from datetime import datetime, timezone
from ai.chunking.chem_entity_extractor import extract_chemical_entities
from ai.chunking.latex_chem_chunker import LaTeXChemistryChunker
from ai.schemas.document import DocumentMetadata
from ai.schemas.ingestion import (
    IngestedDocument,
    ParsedPage,
    ExtractedBlock,
    BlockType,
)

class TestChemEntityExtractor(unittest.TestCase):

    def test_extract_formulas_and_solvents(self):
        text = (
            "The reaction was carried out in THF at 25 °C using C6H12O6 and H2SO4. "
            "Purification with DCM and EtOAc yielded compound 3a."
        )
        entities = extract_chemical_entities(text)
        self.assertIn("THF", entities)
        self.assertIn("DCM", entities)
        self.assertIn("EtOAc", entities)
        self.assertIn("C6H12O6", entities)
        self.assertIn("H2SO4", entities)

    def test_extract_smiles_and_iupac(self):
        text = "SMILES candidate CC(=O)Oc1ccccc1C(=O)O was analyzed for aspirin (acetylsalicylic acid)."
        entities = extract_chemical_entities(text)
        self.assertTrue(any("CC(=O)" in e for e in entities))

class TestLaTeXChemistryChunker(unittest.TestCase):

    def setUp(self):
        self.chunker = LaTeXChemistryChunker(target_chunk_size=300, chunk_overlap=50)

    def test_equation_atomic_preservation(self):
        page = ParsedPage(
            page_number=1,
            text="Intro text.",
            blocks=[
                ExtractedBlock(
                    block_id="b1",
                    page_number=1,
                    block_type=BlockType.HEADING,
                    text="1. Introduction",
                    section_title="1. Introduction"
                ),
                ExtractedBlock(
                    block_id="b2",
                    page_number=1,
                    block_type=BlockType.TEXT,
                    text="We consider the rate law in THF solvent with C8H10N4O2 catalyst."
                ),
                ExtractedBlock(
                    block_id="b3",
                    page_number=1,
                    block_type=BlockType.EQUATION,
                    text="\\begin{equation}\nk = A \\exp\\left(-\\frac{E_a}{RT}\\right)\n\\end{equation}"
                ),
                ExtractedBlock(
                    block_id="b4",
                    page_number=1,
                    block_type=BlockType.TEXT,
                    text="Where k is the rate constant and Ea is activation energy."
                )
            ]
        )
        doc = IngestedDocument(
            document_id="doc_chem_1",
            workspace_id="ws_1",
            filename="paper.pdf",
            metadata=DocumentMetadata(title="Paper Title", created_at=datetime.now(timezone.utc)),
            pages=[page],
            total_pages=1,
            total_blocks=4
        )

        chunks = self.chunker.chunk_document(doc)
        self.assertTrue(len(chunks) >= 2)

        # Check equation chunk
        eq_chunks = [c for c in chunks if c.chunk_type == "equation"]
        self.assertEqual(len(eq_chunks), 1)
        self.assertIn("\\begin{equation}", eq_chunks[0].text)
        self.assertIn("\\end{equation}", eq_chunks[0].text)
        self.assertEqual(eq_chunks[0].page_number, 1)

    def test_section_and_chemical_entity_tagging(self):
        page = ParsedPage(
            page_number=2,
            text="Methods text",
            blocks=[
                ExtractedBlock(
                    block_id="b1",
                    page_number=2,
                    block_type=BlockType.HEADING,
                    text="2. Experimental Methods",
                    section_title="2. Experimental Methods"
                ),
                ExtractedBlock(
                    block_id="b2",
                    page_number=2,
                    block_type=BlockType.TEXT,
                    text="Synthesis was performed in CDCl3 using NaHCO3 and Pd(PPh3)4."
                )
            ]
        )
        doc = IngestedDocument(
            document_id="doc_chem_2",
            workspace_id="ws_1",
            filename="paper2.pdf",
            metadata=DocumentMetadata(title="Paper 2", created_at=datetime.now(timezone.utc)),
            pages=[page],
            total_pages=1,
            total_blocks=2
        )

        chunks = self.chunker.chunk_document(doc)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].section_title, "2. Experimental Methods")
        self.assertIn("CDCl3", chunks[0].chemical_entities)
        self.assertIn("NaHCO3", chunks[0].chemical_entities)
        self.assertIn("Pd(PPh3)4", chunks[0].chemical_entities)

if __name__ == "__main__":
    unittest.main()
