import asyncio
import unittest
from ai.schemas.vector import VectorPoint
from ai.vector_store.mock_store import MockVectorStore, cosine_similarity

class TestVectorStore(unittest.TestCase):

    def test_cosine_similarity_math(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)
        self.assertAlmostEqual(cosine_similarity(v1, v3), 0.0)

    def test_mock_vector_store_crud_and_search(self):
        async def run_test():
            store = MockVectorStore()
            coll_name = "test_chem_collection"

            points = [
                VectorPoint(
                    id="chunk_1",
                    vector=[0.9, 0.1, 0.0],
                    payload={"workspace_id": "ws_1", "document_id": "doc_a", "text": "Synthesis of Benzene in THF.", "page_number": 1, "chemical_entities": ["THF"]}
                ),
                VectorPoint(
                    id="chunk_2",
                    vector=[0.0, 0.9, 0.1],
                    payload={"workspace_id": "ws_1", "document_id": "doc_b", "text": "Quantum mechanics equation.", "page_number": 3, "chemical_entities": []}
                ),
                VectorPoint(
                    id="chunk_3",
                    vector=[0.85, 0.15, 0.0],
                    payload={"workspace_id": "ws_2", "document_id": "doc_c", "text": "DCM solvent reaction.", "page_number": 2, "chemical_entities": ["DCM"]}
                ),
            ]

            await store.upsert_points(coll_name, points)

            # Search with workspace filter for ws_1
            query = [1.0, 0.0, 0.0]
            results = await store.search(coll_name, query_vector=query, limit=5, workspace_id="ws_1")
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].chunk_id, "chunk_1")
            self.assertIn("THF", results[0].chemical_entities)

            # Search with document filter
            doc_results = await store.search(coll_name, query_vector=query, limit=5, document_ids=["doc_a"])
            self.assertEqual(len(doc_results), 1)
            self.assertEqual(doc_results[0].document_id, "doc_a")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
