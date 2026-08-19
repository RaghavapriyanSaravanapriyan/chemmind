from typing import List, Optional
from ai.generation.gateway import LLMGateway, gateway as default_gateway
from ai.schemas.document import DocumentChunk
from ai.schemas.embedding import EmbeddingRequest
from ai.schemas.vector import VectorPoint
from ai.vector_store.base import BaseVectorStore
from ai.utils.logger import logger

class EmbeddingPipeline:
    """
    Pipeline for vector embedding generation and vector database indexing.
    Converts DocumentChunks into dense vector points with full citation metadata payloads.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        llm_gateway: Optional[LLMGateway] = None
    ):
        self.vector_store = vector_store
        self.gateway = llm_gateway or default_gateway

    async def embed_and_index_chunks(
        self,
        collection_name: str,
        chunks: List[DocumentChunk],
        batch_size: int = 32
    ) -> int:
        """
        Embeds a list of DocumentChunks and indexes them into the specified vector store collection.
        Returns total count of indexed chunks.
        """
        if not chunks:
            logger.warning("No document chunks provided to EmbeddingPipeline.")
            return 0

        logger.info(f"Starting batch embedding & indexing for {len(chunks)} chunks into collection '{collection_name}'")
        total_indexed = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]

            # Generate embeddings via LLMGateway
            embed_req = EmbeddingRequest(input_texts=texts)
            embed_resp = await self.gateway.embed(embed_req)

            points: List[VectorPoint] = []
            for chunk, vec in zip(batch, embed_resp.embeddings):
                payload = {
                    "workspace_id": chunk.workspace_id,
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "page_number": chunk.page_number,
                    "page_start": chunk.page_start or chunk.page_number,
                    "page_end": chunk.page_end or chunk.page_number,
                    "section_title": chunk.section_title,
                    "parent_section": chunk.parent_section,
                    "chunk_type": chunk.chunk_type,
                    "chemical_entities": chunk.chemical_entities,
                    "token_count_estimate": chunk.token_count_estimate,
                }

                pt = VectorPoint(
                    id=chunk.chunk_id,
                    vector=vec,
                    payload=payload
                )
                points.append(pt)

            # Ensure collection exists
            vector_dim = len(embed_resp.embeddings[0]) if embed_resp.embeddings else 384
            await self.vector_store.create_collection(collection_name, vector_dim)

            # Upsert into vector store
            await self.vector_store.upsert_points(collection_name, points)
            total_indexed += len(points)

        logger.info(f"Successfully embedded and indexed {total_indexed} chunks into collection '{collection_name}'")
        return total_indexed
