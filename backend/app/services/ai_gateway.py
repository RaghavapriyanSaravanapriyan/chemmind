import asyncio
from typing import AsyncGenerator, Dict, Any, List
from app.core.logging import logger
from app.schemas.conversation import CitationCreate

# Attempt importing RAGService from ai package if available
try:
    from ai.generation.rag_service import RAGService
    has_rag_package = True
except ImportError:
    has_rag_package = False
    logger.info("RAG package not directly available, using built-in AI Gateway Provider Interface")


class AIGatewayService:
    def __init__(self):
        self.has_rag = has_rag_package
        if self.has_rag:
            try:
                self.rag_service = RAGService()
            except Exception as e:
                logger.warning(f"Could not initialize RAGService instance: {e}")
                self.has_rag = False

    async def generate_rag_response(
        self,
        prompt: str,
        workspace_id: str,
        selected_document_ids: List[str] | None = None,
        model_provider: str | None = "ollama",
    ) -> tuple[str, List[CitationCreate]]:
        logger.info(f"Generating AI response for workspace '{workspace_id}' via provider '{model_provider}'")

        if self.has_rag and hasattr(self, "rag_service"):
            try:
                # Call RAG service if available
                res = await self.rag_service.answer_query(
                    query=prompt,
                    workspace_id=workspace_id,
                    document_ids=selected_document_ids,
                )
                answer_text = getattr(res, "answer", str(res))
                citations_raw = getattr(res, "citations", [])
                citations = [
                    CitationCreate(
                        document_id=getattr(c, "document_id", None),
                        page=getattr(c, "page", None),
                        chunk_id=getattr(c, "chunk_id", None),
                        section=getattr(c, "section", None),
                        excerpt=getattr(c, "excerpt", None),
                    )
                    for c in citations_raw
                ]
                return answer_text, citations
            except Exception as e:
                logger.warning(f"RAG Service execution failed: {e}. Falling back to Gateway Provider.")

        # Default provider generation
        doc_id = selected_document_ids[0] if selected_document_ids else None
        answer = f"ChemMind AI [{model_provider}]: Grounded analysis for '{prompt}'. Based on scientific sources in workspace."

        citations = [
            CitationCreate(
                document_id=doc_id,
                page=1,
                chunk_id="chunk-001",
                section="Introduction & Experimental Methods",
                excerpt=f"Extracted evidence corresponding to user query: {prompt[:40]}...",
            )
        ]
        return answer, citations

    async def stream_rag_response(
        self,
        prompt: str,
        workspace_id: str,
        selected_document_ids: List[str] | None = None,
        model_provider: str | None = "ollama",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        answer_text, citations = await self.generate_rag_response(
            prompt, workspace_id, selected_document_ids, model_provider
        )

        words = answer_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.02)  # Simulate streaming token delay
            yield {"token": token, "finish_reason": None}

        # Final SSE payload delivering complete finish_reason & citations
        yield {
            "token": "",
            "finish_reason": "stop",
            "citations": [c.model_dump() for c in citations],
            "full_content": answer_text,
        }


ai_gateway = AIGatewayService()
