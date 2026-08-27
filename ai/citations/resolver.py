import re
from typing import Any, List, Optional, Set
from ai.schemas.citation import Citation, SourceLocation
from ai.schemas.citation_map import CitationMap, CitedRAGResponse
from ai.schemas.rag import RAGResponse
from ai.schemas.retrieval import RetrievedChunk
from ai.utils.logger import logger


class CitationResolver:
    """
    Citation Resolver Engine.
    Parses document citation markers ([1], [2]) and web citation markers ([W1], [Web 1], or Markdown links [Title](URL))
    from generated answer text and maps them to structured Citation objects.
    """

    DOC_CITATION_REGEX = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
    WEB_CITATION_REGEX = re.compile(r"\[W(\d+)\]|\[Web\s*(\d+)\]", re.IGNORECASE)
    MARKDOWN_LINK_REGEX = re.compile(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)")

    def parse_inline_citations(self, text: str) -> List[int]:
        """Parses all unique inline numerical citation indices from generated text."""
        return self.parse_inline_doc_citations(text)

    def parse_inline_doc_citations(self, text: str) -> List[int]:
        """Parses document citation indices (e.g. [1], [1, 2]) from text."""
        indices: Set[int] = set()
        matches = self.DOC_CITATION_REGEX.findall(text)
        for m in matches:
            parts = m.split(",")
            for p in parts:
                p_clean = p.strip()
                if p_clean.isdigit():
                    indices.add(int(p_clean))
        return sorted(list(indices))

    def parse_inline_web_citations(self, text: str) -> List[int]:
        """Parses web citation indices (e.g. [W1], [Web 2]) from text."""
        indices: Set[int] = set()
        matches = self.WEB_CITATION_REGEX.findall(text)
        for m in matches:
            for group in m:
                if group and group.isdigit():
                    indices.add(int(group))
        return sorted(list(indices))

    def resolve_citations(
        self,
        answer: str,
        chunks: List[RetrievedChunk],
        web_results: Optional[List[Any]] = None,
        workspace_id: str = "default_ws",
    ) -> CitationMap:
        """Resolves both document chunks and web search results against answer text citations."""
        citations: List[Citation] = []
        cited_doc_indices = self.parse_inline_doc_citations(answer)
        cited_web_indices = self.parse_inline_web_citations(answer)
        unmapped: List[int] = []

        logger.info(f"Resolving citations: {len(cited_doc_indices)} doc markers, {len(cited_web_indices)} web markers against {len(chunks)} chunks and {len(web_results or [])} web results.")

        # 1. Resolve internal document citations
        for idx in cited_doc_indices:
            if 1 <= idx <= len(chunks):
                chunk = chunks[idx - 1]
                excerpt_text = chunk.text[:200] + ("..." if len(chunk.text) > 200 else "")
                cit = Citation(
                    citation_id=f"cit_{idx}",
                    workspace_id=chunk.workspace_id or workspace_id,
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    document_title=chunk.document_id,
                    title=f"Document Page {chunk.page_number} ({chunk.document_id})",
                    excerpt=excerpt_text,
                    source_type="document",
                    location=SourceLocation(
                        page_number=chunk.page_number,
                        section_title=chunk.section_title
                    )
                )
                citations.append(cit)
            else:
                unmapped.append(idx)

        # 2. Resolve web citations from [W1], [Web 1] markers or all web_results if web search was performed
        if web_results:
            target_indices = cited_web_indices if cited_web_indices else list(range(1, len(web_results) + 1))
            for idx in target_indices:
                if 1 <= idx <= len(web_results):
                    web_res = web_results[idx - 1]
                    title = getattr(web_res, "title", str(web_res))
                    url = getattr(web_res, "url", "#")
                    domain = getattr(web_res, "domain", "web.search")
                    snippet = getattr(web_res, "snippet", "")
                    
                    cit = Citation(
                        citation_id=f"cit_web_{idx}",
                        workspace_id=workspace_id,
                        title=title,
                        url=url,
                        domain=domain,
                        excerpt=snippet[:250] + ("..." if len(snippet) > 250 else ""),
                        source_type="web",
                    )
                    citations.append(cit)

            # 3. Extract explicit Markdown links [Title](https://...) as web citations if not already captured
            md_links = self.MARKDOWN_LINK_REGEX.findall(answer)
            for title, url in md_links:
                if not any(c.url == url for c in citations if c.source_type == "web"):
                    domain = url.split("/")[2] if "://" in url and len(url.split("/")) > 2 else "web.search"
                    cit = Citation(
                        citation_id=f"cit_web_link_{len(citations)+1}",
                        workspace_id=workspace_id,
                        title=title.strip(),
                        url=url.strip(),
                        domain=domain,
                        excerpt=f"Web reference link: {title.strip()} ({url.strip()})",
                        source_type="web",
                    )
                    citations.append(cit)

        return CitationMap(
            citations=citations,
            cited_marker_indices=cited_doc_indices,
            unmapped_markers=unmapped,
        )

    def attach_citations(self, rag_response: RAGResponse) -> CitedRAGResponse:
        """Helper to resolve citations and wrap RAGResponse into a CitedRAGResponse."""
        web_res = getattr(rag_response, "web_results", None)
        citation_map = self.resolve_citations(
            rag_response.answer,
            rag_response.retrieved_chunks,
            web_results=web_res,
            workspace_id=rag_response.workspace_id,
        )
        return CitedRAGResponse(
            answer=rag_response.answer,
            citations=citation_map.citations,
            retrieved_chunks=rag_response.retrieved_chunks,
            usage=rag_response.usage,
            model=rag_response.model,
            workspace_id=rag_response.workspace_id,
        )
