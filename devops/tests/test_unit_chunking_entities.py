import pytest
from ai.chunking.latex_chem_chunker import LaTeXChemistryChunker
from ai.chunking.chem_entity_extractor import extract_chemical_entities
from ai.schemas.document import DocumentMetadata
from ai.schemas.ingestion import IngestedDocument, ParsedPage, ExtractedBlock, BlockType


def test_extract_chemical_entities_solvents_and_reagents():
    text = "The reaction was conducted in DCM and THF at 25 °C using NaBH4 as reducing agent."
    entities = extract_chemical_entities(text)
    assert "DCM" in entities
    assert "THF" in entities
    assert "NaBH4" in entities


def test_extract_chemical_entities_formulas():
    text = "Synthesis of Fe2O3 and C6H12O6 in the presence of H2SO4 and CH3COOH."
    entities = extract_chemical_entities(text)
    assert "Fe2O3" in entities
    assert "C6H12O6" in entities
    assert "H2SO4" in entities
    assert "CH3COOH" in entities


def test_extract_chemical_entities_iupac_terms():
    text = "Substitution on the benzene ring and pyridine ligand afforded an amine derivative."
    entities = extract_chemical_entities(text)
    assert any("benzene" in e.lower() for e in entities)
    assert any("pyridine" in e.lower() for e in entities)
    assert any("amine" in e.lower() for e in entities)


def test_extract_chemical_entities_stop_words_filtered():
    text = "THE REACTION WAS NOT FOR ALL BUT THE NEW DAY."
    entities = extract_chemical_entities(text)
    assert "THE" not in entities
    assert "FOR" not in entities
    assert "PAGE" not in entities


def test_extract_chemical_entities_empty_input():
    assert extract_chemical_entities("") == []
    assert extract_chemical_entities(None) == []


def test_latex_chem_chunker_equation_isolation():
    chunker = LaTeXChemistryChunker(target_chunk_size=300, chunk_overlap=0)
    
    doc = IngestedDocument(
        document_id="doc_test_001",
        workspace_id="ws_001",
        filename="thermodynamics.tex",
        metadata=DocumentMetadata(title="Thermodynamics Paper", checksum="chk123"),
        pages=[
            ParsedPage(
                page_number=1,
                text="Full page text...",
                blocks=[
                    ExtractedBlock(
                        block_id="b1",
                        page_number=1,
                        block_type=BlockType.TEXT,
                        text="The Gibbs free energy of the catalytic cycle is expressed by the standard thermodynamic relation.",
                    ),
                    ExtractedBlock(
                        block_id="b2",
                        page_number=1,
                        block_type=BlockType.EQUATION,
                        text="$$\\Delta G^{\\circ} = \\Delta H^{\\circ} - T\\Delta S^{\\circ}$$",
                    ),
                    ExtractedBlock(
                        block_id="b3",
                        page_number=1,
                        block_type=BlockType.TEXT,
                        text="Where Delta H represents enthalpy and Delta S represents entropy change at temperature T.",
                    ),
                ]
            )
        ]
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 2
    
    # Verify the equation chunk exists with equation chunk_type
    eq_chunk = next((c for c in chunks if "$$\\Delta G^{\\circ}" in c.text), None)
    assert eq_chunk is not None
    assert eq_chunk.chunk_type == "equation"


def test_latex_chem_chunker_section_and_page_tracking():
    chunker = LaTeXChemistryChunker(target_chunk_size=200, chunk_overlap=20)

    doc = IngestedDocument(
        document_id="doc_test_002",
        workspace_id="ws_001",
        filename="catalysis.tex",
        metadata=DocumentMetadata(title="Catalysis Paper", checksum="chk456"),
        pages=[
            ParsedPage(
                page_number=1,
                text="Page 1 text...",
                blocks=[
                    ExtractedBlock(
                        block_id="b1",
                        page_number=1,
                        block_type=BlockType.HEADING,
                        section_title="1. Introduction",
                        text="\\section{1. Introduction}",
                    ),
                    ExtractedBlock(
                        block_id="b2",
                        page_number=1,
                        block_type=BlockType.TEXT,
                        text="Transition metal catalysis in ethanol EtOH provides high enantiomeric excess.",
                    ),
                ]
            ),
            ParsedPage(
                page_number=2,
                text="Page 2 text...",
                blocks=[
                    ExtractedBlock(
                        block_id="b3",
                        page_number=2,
                        block_type=BlockType.HEADING,
                        section_title="2. Experimental Methods",
                        text="\\section{2. Experimental Methods}",
                    ),
                    ExtractedBlock(
                        block_id="b4",
                        page_number=2,
                        block_type=BlockType.TEXT,
                        text="Reaction mixtures were analyzed by NMR in CDCl3 solvent.",
                    ),
                ]
            )
        ]
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 2
    
    # Check that chunks preserve section titles and chemical tags
    assert any(c.section_title == "1. Introduction" for c in chunks)
    assert any(c.section_title == "2. Experimental Methods" for c in chunks)
    assert any("EtOH" in c.chemical_entities for c in chunks)
    assert any("CDCl3" in c.chemical_entities for c in chunks)
