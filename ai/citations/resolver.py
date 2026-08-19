import re
from typing import List, Set
from ai.schemas.citation import Citation, SourceLocation
from ai.schemas.citation_map import CitationMap, CitedRAGResponse
from ai.schemas.rag import RAGResponse
from ai.schemas.retrieval import RetrievedChunk
from ai.utils.logger import logger

class CitationResolver:
    """
    Citation Resolver Engine.
    Parses inline numerical citations (e.g. [1], [2, 3]) from generated text and maps them back
    to exact 1-indexed candidate evidence chunks with structured SourceLocations.
    """

    CITATION_REGEX = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

    def parse_inline_citations(self, text: str) -> List[int]:
        """Parses all unique inline numerical citation indices from generated text."""
        indices: Set[int] = set()
        matches = self.CITATION_REGEX.findall(text)
        
        for m in matches:
            # m can be "1" or "1, 2" or "1,3,4"
            parts = m.split(",")
            for p in parts:
                p_clean = p.strip()
                if p_clean.isdigit():
                    indices.add(int(p_clean))
        
        sorted_indices = sorted(list(indices))
        return sorted_indices

    def resolve_citations(self, answer: str, chunks: List[RetrievedChunk]) -> CitationMap:
        """Resolves inline citation indices against candidate evidence chunks."""
        cited_indices = self.parse_inline_citations(answer)
        citations: List[Citation] = []
        unmapped: List[int] = []

        logger.info(f"Resolving {len(cited_indices)} inline citation markers against {len(chunks)} evidence chunks.")

        for idx in cited_indices:
            # Evidence block indices are 1-indexed
            if 1 <= idx <= len(chunks):
                chunk = chunks[idx - 1]
                excerpt_text = chunk.text[:200] + ("..." if len(chunk.text) > 200 else "")
                
                cit = Citation(
                    citation_id=f"cit_{idx}",
                    workspace_id=chunk.workspace_id,
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    document_title=chunk.document_id,
                    excerpt=excerpt_text,
                    location=SourceLocation(
                        page_number=chunk.page_number,
                        section_title=chunk.section_title
                    )
                )
                citations.append(cit)
            else:
                logger.warning(f"Citation index [{idx}] exceeds available evidence blocks (count: {len(chunks)}).")
                unmapped.append(idx)

        return CitationMap(
            citations=citations,
            cited_marker_indices=cited_indices,
            unmapped_markers=unmapped
        )

    def attach_citations(self, rag_response: RAGResponse) -> CitedRAGResponse:
        """Helper to resolve citations and wrap RAGResponse into a CitedRAGResponse."""
        citation_map = self.resolve_citations(rag_response.answer, rag_response.retrieved_chunks)
        
        return CitedRAGResponse(
            answer=rag_response.answer,
            citations=citation_map.citations,
            retrieved_chunks=rag_response.retrieved_chunks,
            usage=rag_response.usage,
            model=rag_response.model,
            workspace_id=rag_response.workspace_id
        )
