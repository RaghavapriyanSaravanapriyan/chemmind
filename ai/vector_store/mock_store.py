import math
from typing import Dict, List, Optional
from ai.schemas.vector import VectorPoint, VectorSearchResult
from ai.vector_store.base import BaseVectorStore
from ai.utils.logger import logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot / (norm_v1 * norm_v2)

class MockVectorStore(BaseVectorStore):
    """In-memory Mock Vector Store for testing and offline development."""

    def __init__(self):
        # Storage: collection_name -> dict(point_id -> VectorPoint)
        self.collections: Dict[str, Dict[str, VectorPoint]] = {}

    @property
    def store_name(self) -> str:
        return "mock"

    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        if collection_name not in self.collections:
            self.collections[collection_name] = {}
            logger.info(f"Created Mock collection '{collection_name}' (dim: {vector_size})")
        return True

    async def upsert_points(self, collection_name: str, points: List[VectorPoint]) -> bool:
        if collection_name not in self.collections:
            await self.create_collection(collection_name, len(points[0].vector) if points else 384)
        
        for p in points:
            self.collections[collection_name][p.id] = p
        
        logger.info(f"Upserted {len(points)} points into Mock collection '{collection_name}'")
        return True

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        workspace_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        if collection_name not in self.collections:
            return []

        scored_points = []
        for p_id, pt in self.collections[collection_name].items():
            payload = pt.payload or {}
            
            # Apply workspace filter
            if workspace_id and payload.get("workspace_id") != workspace_id:
                continue

            # Apply document list filter
            if document_ids and payload.get("document_id") not in document_ids:
                continue

            score = cosine_similarity(query_vector, pt.vector)
            scored_points.append((score, pt))

        # Sort descending by cosine similarity score
        scored_points.sort(key=lambda x: x[0], reverse=True)
        top_k = scored_points[:limit]

        results = []
        for score, pt in top_k:
            payload = pt.payload or {}
            res = VectorSearchResult(
                chunk_id=str(pt.id),
                score=float(score),
                text=payload.get("text", ""),
                workspace_id=payload.get("workspace_id", ""),
                document_id=payload.get("document_id", ""),
                page_number=payload.get("page_number", 1),
                section_title=payload.get("section_title"),
                chemical_entities=payload.get("chemical_entities", []),
                chunk_type=payload.get("chunk_type", "text"),
                payload=payload
            )
            results.append(res)

        return results

    async def delete_collection(self, collection_name: str) -> bool:
        if collection_name in self.collections:
            del self.collections[collection_name]
            logger.info(f"Deleted Mock collection '{collection_name}'")
        return True
