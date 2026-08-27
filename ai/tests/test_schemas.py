import unittest
from ai.schemas import (
    Role,
    ChatMessage,
    LLMRequest,
    LLMResponse,
    Citation,
    SourceLocation,
    DocumentChunk,
    EmbeddingRequest,
    EmbeddingResponse,
)

class TestSchemas(unittest.TestCase):

    def test_llm_request_and_response(self):
        msg = ChatMessage(role=Role.USER, content="Hello ChemMind")
        req = LLMRequest(messages=[msg], temperature=0.5)
        self.assertEqual(len(req.messages), 1)
        self.assertEqual(req.messages[0].role, Role.USER)
        self.assertEqual(req.temperature, 0.5)

        resp = LLMResponse(content="Hi there!", model="llama3")
        self.assertEqual(resp.content, "Hi there!")
        self.assertEqual(resp.model, "llama3")

    def test_citation_schema(self):
        loc = SourceLocation(page_number=3, section_title="Methods", bbox=[0.1, 0.2, 0.5, 0.6])
        cit = Citation(
            workspace_id="ws_1",
            document_id="doc_1",
            chunk_id="chk_1",
            document_title="Paper A",
            excerpt="Reaction kinetics were observed...",
            location=loc
        )
        self.assertEqual(cit.location.page_number, 3)
        self.assertEqual(cit.location.section_title, "Methods")
        self.assertEqual(cit.document_id, "doc_1")

    def test_document_chunk_schema(self):
        chunk = DocumentChunk(
            chunk_id="c1",
            document_id="d1",
            workspace_id="w1",
            text="Benzene has a planar hexagonal structure.",
            page_number=1,
            chemical_entities=["benzene"]
        )
        self.assertEqual(chunk.chemical_entities, ["benzene"])
        self.assertEqual(chunk.page_number, 1)

    def test_embedding_schemas(self):
        req = EmbeddingRequest(input_texts=["Text 1", "Text 2"])
        self.assertEqual(len(req.input_texts), 2)

        resp = EmbeddingResponse(embeddings=[[0.1, 0.2], [0.3, 0.4]], model="nomic")
        self.assertEqual(len(resp.embeddings), 2)

if __name__ == "__main__":
    unittest.main()
