from typing import Any, AsyncGenerator, Dict, List, Optional
from ai.agentic.router import AgenticRouter, RoutingDecision, RoutingMode
from ai.agentic.tools import ChemistryPropertyTool, InternalDocSearchTool, WebSearchResult, WebSearchTool
from ai.citations.resolver import CitationResolver
from ai.generation.gateway import LLMGateway, gateway as default_gateway
from ai.prompts.chem_rag_prompt import CHEMISTRY_RAG_SYSTEM_PROMPT
from ai.reranking.base import BaseReranker
from ai.retrieval.base import BaseRetriever
from ai.schemas.llm import ChatMessage, LLMRequest, Role
from ai.schemas.rag import RAGRequest, RAGResponse
from ai.schemas.rerank import RerankRequest
from ai.schemas.retrieval import RetrievedChunk
from ai.utils.logger import logger


class AgenticRAGEngine:
    """
    Modern Agentic RAG Engine with Intelligent Tool Selection and Web Access.
    - Evaluates query scope and internal document sufficiency.
    - Conditionally executes Web Search and Chemical Property lookup skills.
    - Synthesizes answers with clean clickable web URLs and document citations.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        llm_gateway: Optional[LLMGateway] = None,
        reranker: Optional[BaseReranker] = None,
        sufficiency_threshold: float = 0.30,
    ):
        self.retriever = retriever
        self.gateway = llm_gateway or default_gateway
        self.reranker = reranker
        self.doc_search_tool = InternalDocSearchTool(retriever)
        self.web_search_tool = WebSearchTool()
        self.chem_tool = ChemistryPropertyTool()
        self.router = AgenticRouter(sufficiency_threshold=sufficiency_threshold)
        self.citation_resolver = CitationResolver()

    async def execute(self, request: RAGRequest) -> RAGResponse:
        logger.info(f"AgenticRAGEngine executing query: '{request.query_text[:60]}' in workspace '{request.workspace_id}'")

        # Step 1: Internal Document Vector Retrieval
        retrieved_chunks = await self.doc_search_tool.search(
            query=request.query_text,
            workspace_id=request.workspace_id,
            collection_name=request.collection_name,
            document_ids=request.document_ids,
            top_k=request.top_k * 2 if self.reranker else request.top_k,
            min_score=request.min_score,
        )

        # Step 2: Rerank internal document chunks if reranker available
        if self.reranker and retrieved_chunks:
            rerank_req = RerankRequest(
                query_text=request.query_text,
                candidate_chunks=retrieved_chunks,
                top_k=request.top_k
            )
            rerank_resp = await self.reranker.rerank(rerank_req)
            retrieved_chunks = [
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

        # Step 3: Agentic Router Evaluation
        decision: RoutingDecision = self.router.evaluate(
            query=request.query_text,
            retrieved_chunks=retrieved_chunks,
            force_web=request.enable_web_search,
        )

        # Step 4: Conditional Web Search Tool Execution
        web_results: List[WebSearchResult] = []
        if decision.should_use_web:
            logger.info(f"AgenticRAGEngine: Invoking WebSearchTool (Routing mode: {decision.mode})")
            web_results = await self.web_search_tool.search(request.query_text, max_results=4)

        # Step 5: Build Agentic System Prompt and Context
        messages = self._build_agentic_prompt(
            query=request.query_text,
            doc_chunks=retrieved_chunks if decision.mode != RoutingMode.WEB_FALLBACK else [],
            web_results=web_results,
            decision=decision,
        )

        # Step 6: Generate LLM Response
        llm_req = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            stream=False,
        )
        llm_resp = await self.gateway.generate(llm_req)

        # Step 7: Resolve Citations (Document & Web Clickable Links)
        cit_map = self.citation_resolver.resolve_citations(
            answer=llm_resp.content,
            chunks=retrieved_chunks,
            web_results=web_results,
            workspace_id=request.workspace_id,
        )

        return RAGResponse(
            answer=llm_resp.content,
            retrieved_chunks=retrieved_chunks,
            web_results=[w.model_dump() for w in web_results],
            citations=[c.model_dump() for c in cit_map.citations],
            routing_mode=decision.mode.value,
            usage=llm_resp.usage,
            model=llm_resp.model,
            workspace_id=request.workspace_id,
        )

    async def stream_execute(self, request: RAGRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming execution yields tokens followed by final web/document metadata."""
        logger.info(f"AgenticRAGEngine streaming query: '{request.query_text[:60]}' in workspace '{request.workspace_id}'")

        retrieved_chunks = await self.doc_search_tool.search(
            query=request.query_text,
            workspace_id=request.workspace_id,
            collection_name=request.collection_name,
            document_ids=request.document_ids,
            top_k=request.top_k,
            min_score=request.min_score,
        )

        decision: RoutingDecision = self.router.evaluate(
            query=request.query_text,
            retrieved_chunks=retrieved_chunks,
            force_web=request.enable_web_search,
        )

        web_results: List[WebSearchResult] = []
        if decision.should_use_web:
            web_results = await self.web_search_tool.search(request.query_text, max_results=4)

        messages = self._build_agentic_prompt(
            query=request.query_text,
            doc_chunks=retrieved_chunks if decision.mode != RoutingMode.WEB_FALLBACK else [],
            web_results=web_results,
            decision=decision,
        )

        llm_req = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            stream=True,
        )

        full_text = ""
        async for chunk in self.gateway.stream(llm_req):
            if chunk.delta_content:
                full_text += chunk.delta_content
                yield {"token": chunk.delta_content, "finish_reason": None}

        # Final metadata payload with resolved citations
        cit_map = self.citation_resolver.resolve_citations(
            answer=full_text,
            chunks=retrieved_chunks,
            web_results=web_results,
            workspace_id=request.workspace_id,
        )

        yield {
            "token": "",
            "finish_reason": "stop",
            "full_content": full_text,
            "citations": [c.model_dump() for c in cit_map.citations],
            "routing_mode": decision.mode.value,
            "web_results": [w.model_dump() for w in web_results],
        }

    def _build_agentic_prompt(
        self,
        query: str,
        doc_chunks: List[RetrievedChunk],
        web_results: List[WebSearchResult],
        decision: RoutingDecision,
    ) -> List[ChatMessage]:
        system_instruction = (
            f"{CHEMISTRY_RAG_SYSTEM_PROMPT}\n"
            "ADDITIONAL AGENTIC WEB & CITATION INSTRUCTIONS:\n"
            "1. If web evidence blocks are provided, synthesize the latest internet/scientific information.\n"
            "2. Whenever referring to web sources, format every inline web citation as a clean, clickable Markdown link using the format: `[Title/Domain](URL)` (e.g. `[PubChem Compound Record](https://pubchem.ncbi.nlm.nih.gov/...)` or `[ACS Journal](https://pubs.acs.org/...)`).\n"
            "3. Whenever derived from internal document evidence blocks, use bracketed document numerical markers like `[1]`, `[2]`.\n"
            "4. Combine document and web information seamlessly into a professional, highly grounded scientific answer.\n"
        )

        context_blocks = []
        if doc_chunks:
            context_blocks.append("=== INTERNAL WORKSPACE DOCUMENT EVIDENCE ===")
            for idx, chunk in enumerate(doc_chunks, start=1):
                sec = f" (Section: {chunk.section_title})" if chunk.section_title else ""
                context_blocks.append(
                    f"--- DOCUMENT EVIDENCE BLOCK [{idx}] ---\n"
                    f"Document ID: {chunk.document_id} | Page: {chunk.page_number}{sec}\n"
                    f"{chunk.text}\n"
                )

        if web_results:
            context_blocks.append("=== LIVE WEB & SCIENTIFIC INTERNET SEARCH EVIDENCE ===")
            for idx, web_res in enumerate(web_results, start=1):
                context_blocks.append(
                    f"--- WEB SEARCH BLOCK [W{idx}] ---\n"
                    f"Title: {web_res.title}\n"
                    f"URL: {web_res.url}\n"
                    f"Domain: {web_res.domain}\n"
                    f"Snippet: {web_res.snippet}\n"
                )

        formatted_context = "\n".join(context_blocks) if context_blocks else "NO EVIDENCE BLOCKS AVAILABLE."

        user_content = (
            f"AGENTIC ROUTING DECISION: {decision.mode.value.upper()} ({decision.reason})\n\n"
            f"AVAILABLE EVIDENCE CONTEXT:\n"
            f"{formatted_context}\n\n"
            f"USER QUESTION:\n"
            f"{query}"
        )

        return [
            ChatMessage(role=Role.SYSTEM, content=system_instruction),
            ChatMessage(role=Role.USER, content=user_content),
        ]
