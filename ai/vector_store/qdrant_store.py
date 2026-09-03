from typing import List, Optional
import uuid
from qdrant_client import AsyncQdrantClient, models
from ai.config import settings
from ai.schemas.vector import VectorPoint, VectorSearchResult
from ai.vector_store.base import BaseVectorStore
from ai.utils.logger import logger


def _qdrant_point_id(chunk_id: str):
    """Qdrant point IDs must be UUID or uint. Map arbitrary chunk_ids
    deterministically to UUIDv5 so string IDs like 'c1' work."""
    try:
        return str(uuid.UUID(str(chunk_id)))
    except (ValueError, AttributeError, TypeError):
        pass
    try:
        # Unsigned int strings are valid as-is if they fit uint64.
        iv = int(str(chunk_id))
        if iv >= 0:
            return iv
    except (ValueError, TypeError):
        pass
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"chemmind:{chunk_id}"))

class QdrantVectorStore(BaseVectorStore):
    """Concrete Qdrant Vector Store implementation via AsyncQdrantClient."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, url: Optional[str] = None):
        target_url = url or getattr(settings, "qdrant_url", None)
        if target_url:
            self.client = AsyncQdrantClient(url=target_url)
        else:
            self.client = AsyncQdrantClient(
                host=host or settings.qdrant_host,
                port=port or settings.qdrant_port
            )

    @property
    def store_name(self) -> str:
        return "qdrant"

    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        logger.info(f"Creating Qdrant collection '{collection_name}' (dim: {vector_size})")
        exists = await self.client.collection_exists(collection_name=collection_name)
        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection '{collection_name}' successfully")
        return True

    async def upsert_points(self, collection_name: str, points: List[VectorPoint]) -> bool:
        if not points:
            return True
        logger.info(f"Upserting {len(points)} vector points into Qdrant collection '{collection_name}'")
        
        q_points = []
        for p in points:
            payload = dict(p.payload or {})
            # Preserve original chunk_id for retrieval; Qdrant ID is derived.
            payload.setdefault("chunk_id", p.id)
            q_points.append(
                models.PointStruct(
                    id=_qdrant_point_id(p.id),
                    vector=p.vector,
                    payload=payload
                )
            )
        
        await self.client.upsert(
            collection_name=collection_name,
            points=q_points
        )
        return True

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        workspace_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        must_conditions = []
        if workspace_id:
            must_conditions.append(
                models.FieldCondition(
                    key="workspace_id",
                    match=models.MatchValue(value=workspace_id)
                )
            )
        if document_ids:
            must_conditions.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchAny(any=document_ids)
                )
            )

        search_filter = models.Filter(must=must_conditions) if must_conditions else None

        results = await self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        )

        search_results: List[VectorSearchResult] = []
        for point in results.points:
            payload = point.payload or {}
            res = VectorSearchResult(
                chunk_id=str(payload.get("chunk_id", point.id)),
                score=float(point.score),
                text=payload.get("text", ""),
                workspace_id=payload.get("workspace_id", ""),
                document_id=payload.get("document_id", ""),
                page_number=payload.get("page_number", 1),
                section_title=payload.get("section_title"),
                chemical_entities=payload.get("chemical_entities", []),
                chunk_type=payload.get("chunk_type", "text"),
                payload=payload
            )
            search_results.append(res)

        return search_results

    async def delete_collection(self, collection_name: str) -> bool:
        logger.info(f"Deleting Qdrant collection '{collection_name}'")
        return await self.client.delete_collection(collection_name=collection_name)
