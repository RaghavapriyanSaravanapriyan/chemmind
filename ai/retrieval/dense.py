from typing import List, Optional
from ai.generation.gateway import LLMGateway, gateway as default_gateway
from ai.retrieval.base import BaseRetriever
from ai.schemas.embedding import EmbeddingRequest
from ai.schemas.retrieval import RetrievalQuery, RetrievedChunk, RetrievalResponse
from ai.vector_store.base import BaseVectorStore
from ai.utils.logger import logger

class DenseRetriever(BaseRetriever):
    """
    Dense Vector Retriever performing similarity search over indexed vector collections.
    Supports strict workspace isolation, score threshold filtering, and chemical tag pre-filtering.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        llm_gateway: Optional[LLMGateway] = None
    ):
        self.vector_store = vector_store
        self.gateway = llm_gateway or default_gateway

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        logger.info(
            f"Executing dense retrieval for query '{query.query_text[:50]}...' in workspace '{query.workspace_id}' (top_k={query.top_k})"
        )

        # 1. Embed query string via gateway
        embed_req = EmbeddingRequest(input_texts=[query.query_text])
        embed_resp = await self.gateway.embed(embed_req)
        
        if not embed_resp.embeddings:
            logger.error("Failed to generate embedding vector for retrieval query.")
            return RetrievalResponse(
                query_text=query.query_text,
                workspace_id=query.workspace_id,
                results=[],
                total_retrieved=0
            )

        query_vector = embed_resp.embeddings[0]

        # 2. Query vector store with strict workspace_id & document_ids filters
        raw_results = await self.vector_store.search(
            collection_name=query.collection_name,
            query_vector=query_vector,
            limit=query.top_k * 2,  # Fetch extra candidates for post-filtering
            workspace_id=query.workspace_id,
            document_ids=query.document_ids
        )

        # 3. Post-filter by min_score threshold and optional chemical_filter
        filtered_results: List[RetrievedChunk] = []

        for item in raw_results:
            if item.score < query.min_score:
                continue

            # Chemical filter check
            if query.chemical_filter:
                chunk_chem = {c.upper() for c in item.chemical_entities}
                req_chem = {c.upper() for c in query.chemical_filter}
                if not req_chem.issubset(chunk_chem):
                    continue

            retrieved_item = RetrievedChunk(
                chunk_id=item.chunk_id,
                score=item.score,
                text=item.text,
                document_id=item.document_id,
                workspace_id=item.workspace_id,
                page_number=item.page_number,
                page_start=item.payload.get("page_start", item.page_number),
                page_end=item.payload.get("page_end", item.page_number),
                section_title=item.section_title,
                chemical_entities=item.chemical_entities,
                chunk_type=item.chunk_type,
                payload=item.payload
            )
            filtered_results.append(retrieved_item)

            if len(filtered_results) >= query.top_k:
                break

        logger.info(
            f"Dense retrieval returned {len(filtered_results)} candidate chunks for workspace '{query.workspace_id}'"
        )

        return RetrievalResponse(
            query_text=query.query_text,
            workspace_id=query.workspace_id,
            results=filtered_results,
            total_retrieved=len(filtered_results)
        )
