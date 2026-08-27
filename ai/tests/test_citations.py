import unittest
from ai.citations.resolver import CitationResolver
from ai.schemas.rag import RAGResponse
from ai.schemas.retrieval import RetrievedChunk

class TestCitationResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = CitationResolver()

    def test_parse_inline_citations(self):
        text = "Aspirin synthesis requires THF solvent [1]. Reaction occurs at 50 °C [2, 3] with high yield [1, 4]."
        parsed_indices = self.resolver.parse_inline_citations(text)

        self.assertEqual(parsed_indices, [1, 2, 3, 4])

    def test_resolve_citations_and_attach(self):
        answer = "Benzene is nitrated using H2SO4 catalyst [1]. The reaction temperature is maintained at 60 °C [2]. Invalid marker [99]."
        
        chunks = [
            RetrievedChunk(
                chunk_id="chunk_10",
                score=0.95,
                text="Nitration of Benzene takes place using nitric acid in sulfuric acid catalyst.",
                document_id="doc_a",
                workspace_id="ws_1",
                page_number=2,
                section_title="Methods",
                chemical_entities=["Benzene", "H2SO4"]
            ),
            RetrievedChunk(
                chunk_id="chunk_20",
                score=0.88,
                text="Maintain internal reaction temperature at 60 °C for optimal yield.",
                document_id="doc_a",
                workspace_id="ws_1",
                page_number=3,
                section_title="Experimental",
                chemical_entities=[]
            ),
        ]

        citation_map = self.resolver.resolve_citations(answer, chunks)

        self.assertEqual(len(citation_map.citations), 2)
        self.assertEqual(citation_map.cited_marker_indices, [1, 2, 99])
        self.assertEqual(citation_map.unmapped_markers, [99])

        # Verify Citation 1
        cit1 = citation_map.citations[0]
        self.assertEqual(cit1.citation_id, "cit_1")
        self.assertEqual(cit1.chunk_id, "chunk_10")
        self.assertEqual(cit1.location.page_number, 2)
        self.assertEqual(cit1.location.section_title, "Methods")

        # Test attach_citations helper
        rag_resp = RAGResponse(
            answer=answer,
            retrieved_chunks=chunks,
            model="mock-model",
            workspace_id="ws_1"
        )
        cited_resp = self.resolver.attach_citations(rag_resp)

        self.assertEqual(len(cited_resp.citations), 2)
        self.assertEqual(cited_resp.answer, answer)
        self.assertEqual(cited_resp.workspace_id, "ws_1")

if __name__ == "__main__":
    unittest.main()
