from typing import AsyncGenerator, Optional, List
from ai.generation.gateway import LLMGateway, gateway as default_gateway
from ai.prompts.chem_rag_prompt import build_rag_prompt
from ai.reranking.base import BaseReranker
from ai.retrieval.base import BaseRetriever
from ai.schemas.llm import LLMRequest
from ai.schemas.rag import RAGRequest, RAGResponse
from ai.schemas.rerank import RerankRequest
from ai.schemas.retrieval import RetrievalQuery, RetrievedChunk
from ai.utils.logger import logger

class RAGGenerationService:
    """
    RAG Generation Orchestrator Service.
    Connects Retrieval engine, Reranker, Prompt construction, and LLM Gateway for sync/streaming RAG Q&A.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        llm_gateway: Optional[LLMGateway] = None,
        reranker: Optional[BaseReranker] = None
    ):
        self.retriever = retriever
        self.gateway = llm_gateway or default_gateway
        self.reranker = reranker

    async def generate(self, request: RAGRequest) -> RAGResponse:
        logger.info(f"RAG generate request for query: '{request.query_text[:50]}...' in workspace '{request.workspace_id}'")

        # 1. Execute Retrieval
        ret_query = RetrievalQuery(
            query_text=request.query_text,
            workspace_id=request.workspace_id,
            collection_name=request.collection_name,
            document_ids=request.document_ids,
            top_k=request.top_k * 2 if self.reranker else request.top_k,
            min_score=request.min_score,
        )
        ret_response = await self.retriever.retrieve(ret_query)
        candidate_chunks = ret_response.results

        # 2. Execute Reranking if configured
        if self.reranker and candidate_chunks:
            rerank_req = RerankRequest(
                query_text=request.query_text,
                candidate_chunks=candidate_chunks,
                top_k=request.top_k
            )
            rerank_resp = await self.reranker.rerank(rerank_req)
            # Map reranked chunks back to RetrievedChunk items
            candidate_chunks = [
                RetrievedChunk(
                    chunk_id=r.chunk_id,
                    score=r.rerank_score,
                    text=r.text,
                    document_id=r.document_id,
                    workspace_id=r.workspace_id,
                    page_number=r.page_number,
                    page_start=r.page_start,
                    page_end=r.page_end,
                    section_title=r.section_title,
                    chemical_entities=r.chemical_entities,
                    chunk_type=r.chunk_type,
                    payload=r.payload
                ) for r in rerank_resp.results
            ]

        # 3. Build RAG prompt messages
        messages = build_rag_prompt(request.query_text, candidate_chunks)

        # 4. Invoke LLM Gateway
        llm_req = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            stream=False,
        )
        llm_resp = await self.gateway.generate(llm_req)

        return RAGResponse(
            answer=llm_resp.content,
            retrieved_chunks=candidate_chunks,
            usage=llm_resp.usage,
            model=llm_resp.model,
            workspace_id=request.workspace_id,
        )

    async def stream(self, request: RAGRequest) -> AsyncGenerator[str, None]:
        logger.info(f"RAG streaming request for query: '{request.query_text[:50]}...' in workspace '{request.workspace_id}'")

        # 1. Execute Retrieval
        ret_query = RetrievalQuery(
            query_text=request.query_text,
            workspace_id=request.workspace_id,
            collection_name=request.collection_name,
            document_ids=request.document_ids,
            top_k=request.top_k * 2 if self.reranker else request.top_k,
            min_score=request.min_score,
        )
        ret_response = await self.retriever.retrieve(ret_query)
        candidate_chunks = ret_response.results

        # 2. Execute Reranking if configured
        if self.reranker and candidate_chunks:
            rerank_req = RerankRequest(
                query_text=request.query_text,
                candidate_chunks=candidate_chunks,
                top_k=request.top_k
            )
            rerank_resp = await self.reranker.rerank(rerank_req)
            candidate_chunks = [
                RetrievedChunk(
                    chunk_id=r.chunk_id,
                    score=r.rerank_score,
                    text=r.text,
                    document_id=r.document_id,
                    workspace_id=r.workspace_id,
                    page_number=r.page_number,
                    page_start=r.page_start,
                    page_end=r.page_end,
                    section_title=r.section_title,
                    chemical_entities=r.chemical_entities,
                    chunk_type=r.chunk_type,
                    payload=r.payload
                ) for r in rerank_resp.results
            ]

        # 3. Build RAG prompt messages
        messages = build_rag_prompt(request.query_text, candidate_chunks)

        # 4. Invoke Streaming LLM Gateway
        llm_req = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            stream=True,
        )
        async for chunk in self.gateway.stream(llm_req):
            if chunk.delta_content:
                yield chunk.delta_content
