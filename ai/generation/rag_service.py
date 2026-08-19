from typing import AsyncGenerator, Optional
from ai.generation.gateway import LLMGateway, gateway as default_gateway
from ai.prompts.chem_rag_prompt import build_rag_prompt
from ai.retrieval.base import BaseRetriever
from ai.schemas.llm import LLMRequest
from ai.schemas.rag import RAGRequest, RAGResponse
from ai.schemas.retrieval import RetrievalQuery
from ai.utils.logger import logger

class RAGGenerationService:
    """
    RAG Generation Orchestrator Service.
    Connects Retrieval engine, Prompt construction, and LLM Gateway for sync/streaming RAG Q&A.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        llm_gateway: Optional[LLMGateway] = None
    ):
        self.retriever = retriever
        self.gateway = llm_gateway or default_gateway

    async def generate(self, request: RAGRequest) -> RAGResponse:
        logger.info(f"RAG generate request for query: '{request.query_text[:50]}...' in workspace '{request.workspace_id}'")

        # 1. Execute Retrieval
        ret_query = RetrievalQuery(
            query_text=request.query_text,
            workspace_id=request.workspace_id,
            collection_name=request.collection_name,
            document_ids=request.document_ids,
            top_k=request.top_k,
            min_score=request.min_score,
        )
        ret_response = await self.retriever.retrieve(ret_query)

        # 2. Build RAG prompt messages
        messages = build_rag_prompt(request.query_text, ret_response.results)

        # 3. Invoke LLM Gateway
        llm_req = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            stream=False,
        )
        llm_resp = await self.gateway.generate(llm_req)

        return RAGResponse(
            answer=llm_resp.content,
            retrieved_chunks=ret_response.results,
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
            top_k=request.top_k,
            min_score=request.min_score,
        )
        ret_response = await self.retriever.retrieve(ret_query)

        # 2. Build RAG prompt messages
        messages = build_rag_prompt(request.query_text, ret_response.results)

        # 3. Invoke Streaming LLM Gateway
        llm_req = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            stream=True,
        )
        async for chunk in self.gateway.stream(llm_req):
            if chunk.delta_content:
                yield chunk.delta_content
