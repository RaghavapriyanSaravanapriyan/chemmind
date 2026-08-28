import pytest
from ai.citations.resolver import CitationResolver
from ai.schemas.retrieval import RetrievedChunk
from ai.agentic.tools import WebSearchResult


@pytest.fixture
def resolver():
    return CitationResolver()


def test_parse_inline_doc_citations(resolver: CitationResolver):
    text = "The catalyst exhibited 98% yield [1], which matches earlier reports [2, 3]."
    indices = resolver.parse_inline_doc_citations(text)
    assert indices == [1, 2, 3]


def test_parse_inline_web_citations(resolver: CitationResolver):
    text = "Recent literature [W1] and external databases [Web 2] confirm the reaction kinetics."
    indices = resolver.parse_inline_web_citations(text)
    assert indices == [1, 2]


def test_resolve_citations_document_mapping(resolver: CitationResolver):
    chunks = [
        RetrievedChunk(
            chunk_id="chunk_1",
            document_id="doc_thermo_001",
            workspace_id="ws_001",
            score=0.92,
            text="Gibbs free energy of reaction is negative at standard conditions.",
            page_number=3,
            section_title="Thermodynamics Results",
        ),
        RetrievedChunk(
            chunk_id="chunk_2",
            document_id="doc_thermo_001",
            workspace_id="ws_001",
            score=0.88,
            text="Enthalpy change was measured using differential scanning calorimetry.",
            page_number=5,
            section_title="Calorimetry",
        ),
    ]

    answer = "The reaction is spontaneous [1] as verified by calorimetry [2]."
    citation_map = resolver.resolve_citations(answer, chunks, workspace_id="ws_001")

    assert len(citation_map.citations) == 2
    assert citation_map.cited_marker_indices == [1, 2]
    assert citation_map.unmapped_markers == []

    cit1 = citation_map.citations[0]
    assert cit1.document_id == "doc_thermo_001"
    assert cit1.location.page_number == 3
    assert cit1.location.section_title == "Thermodynamics Results"
    assert "Gibbs free energy" in cit1.excerpt

    cit2 = citation_map.citations[1]
    assert cit2.location.page_number == 5


def test_resolve_citations_unmapped_marker_handling(resolver: CitationResolver):
    chunks = [
        RetrievedChunk(
            chunk_id="chunk_1",
            document_id="doc_001",
            workspace_id="ws_001",
            score=0.9,
            text="Sample chunk 1",
            page_number=1,
        )
    ]

    # LLM hallucinates citation marker [5] which does not exist in candidate chunks
    answer = "This finding is discussed in [1] and also in [5]."
    citation_map = resolver.resolve_citations(answer, chunks, workspace_id="ws_001")

    assert len(citation_map.citations) == 1
    assert 5 in citation_map.unmapped_markers


def test_resolve_citations_web_markdown_links(resolver: CitationResolver):
    web_results = [
        WebSearchResult(
            title="PubChem Benzene",
            url="https://pubchem.ncbi.nlm.nih.gov/compound/241",
            snippet="Benzene is an aromatic hydrocarbon with molecular formula C6H6.",
            domain="pubchem.ncbi.nlm.nih.gov",
        )
    ]

    answer = (
        "Benzene is an aromatic ring [W1]. Detailed compound attributes are available at "
        "[PubChem Record](https://pubchem.ncbi.nlm.nih.gov/compound/241)."
    )

    citation_map = resolver.resolve_citations(answer, [], web_results=web_results, workspace_id="ws_001")
    assert len(citation_map.citations) >= 1
    
    web_cit = next((c for c in citation_map.citations if c.source_type == "web"), None)
    assert web_cit is not None
    assert "pubchem.ncbi.nlm.nih.gov" in web_cit.url
