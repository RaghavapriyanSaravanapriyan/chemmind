from typing import List, Optional
from ai.retrieval.base import BaseRetriever
from ai.retrieval.dense import DenseRetriever
from ai.retrieval.rrf import reciprocal_rank_fusion
from ai.retrieval.sparse import BM25KeywordRetriever
from ai.schemas.document import DocumentChunk
from ai.schemas.retrieval import RetrievalQuery, RetrievedChunk, RetrievalResponse
from ai.utils.logger import logger

class HybridRetriever(BaseRetriever):
    """
    Hybrid Retriever combining Dense Vector similarity search and BM25 Sparse Keyword search
    via Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: Optional[BM25KeywordRetriever] = None,
        rrf_k: int = 60
    ):
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever or BM25KeywordRetriever()
        self.rrf_k = rrf_k

    async def retrieve(
        self,
        query: RetrievalQuery,
        candidate_chunks: Optional[List[DocumentChunk]] = None
    ) -> RetrievalResponse:
        logger.info(f"Executing Hybrid Retrieval for query '{query.query_text[:50]}...' in workspace '{query.workspace_id}'")

        # 1. Execute Dense Retrieval
        dense_response = await self.dense_retriever.retrieve(query)
        dense_results = dense_response.results

        # 2. Execute BM25 Sparse Keyword Retrieval if candidate_chunks are supplied
        sparse_results: List[RetrievedChunk] = []
        if candidate_chunks:
            # Filter candidate chunks by workspace_id & document_ids
            filtered_candidates = [
                c for c in candidate_chunks
                if c.workspace_id == query.workspace_id
                and (not query.document_ids or c.document_id in query.document_ids)
            ]
            sparse_results = self.bm25_retriever.rank_chunks(
                query_text=query.query_text,
                chunks=filtered_candidates,
                top_k=query.top_k * 2
            )

        # 3. If no separate sparse candidates provided, extract sparse results from dense results
        if not sparse_results and dense_results:
            # Convert retrieved items to DocumentChunk for BM25 ranking
            dense_as_chunks = [
                DocumentChunk(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    workspace_id=r.workspace_id,
                    text=r.text,
                    page_number=r.page_number,
                    section_title=r.section_title,
                    chemical_entities=r.chemical_entities,
                    chunk_type=r.chunk_type
                ) for r in dense_results
            ]
            sparse_results = self.bm25_retriever.rank_chunks(
                query_text=query.query_text,
                chunks=dense_as_chunks,
                top_k=query.top_k * 2
            )

        # 4. Perform Reciprocal Rank Fusion (RRF)
        if sparse_results:
            fused = reciprocal_rank_fusion(dense_results, sparse_results, k=self.rrf_k)
        else:
            fused = dense_results

        # 5. Filter top_k
        final_results = fused[:query.top_k]

        logger.info(f"Hybrid retrieval completed returning {len(final_results)} chunks for workspace '{query.workspace_id}'")

        return RetrievalResponse(
            query_text=query.query_text,
            workspace_id=query.workspace_id,
            results=final_results,
            total_retrieved=len(final_results)
        )
