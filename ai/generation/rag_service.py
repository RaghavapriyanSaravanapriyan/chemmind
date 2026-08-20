from typing import AsyncGenerator, Optional, List
from ai.agentic.agent import AgenticRAGEngine
from ai.generation.gateway import LLMGateway, gateway as default_gateway
from ai.reranking.base import BaseReranker
from ai.retrieval.base import BaseRetriever
from ai.schemas.rag import RAGRequest, RAGResponse
from ai.utils.logger import logger


class RAGGenerationService:
    """
    RAG Generation Orchestrator Service.
    Powered by AgenticRAGEngine with Web Access Tools, Reranking, and Clickable Web Citations.
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
        self.agentic_engine = AgenticRAGEngine(
            retriever=retriever,
            llm_gateway=self.gateway,
            reranker=reranker,
        )

    async def generate(self, request: RAGRequest) -> RAGResponse:
        logger.info(f"RAG Generation Service handling query via Agentic Engine: '{request.query_text[:50]}...'")
        return await self.agentic_engine.execute(request)

    async def stream(self, request: RAGRequest) -> AsyncGenerator[str, None]:
        logger.info(f"RAG Generation Service streaming query via Agentic Engine: '{request.query_text[:50]}...'")
        async for chunk_payload in self.agentic_engine.stream_execute(request):
            if chunk_payload.get("token"):
                yield chunk_payload["token"]
