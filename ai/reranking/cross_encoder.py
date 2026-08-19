import re
from typing import List
from ai.reranking.base import BaseReranker
from ai.retrieval.sparse import tokenize_chemistry_text
from ai.schemas.rerank import RerankRequest, RerankedChunk, RerankResponse
from ai.utils.logger import logger

ACTIONABLE_SECTIONS = {"methods", "experimental", "synthesis", "results", "discussion", "thermodynamics", "kinetics"}

class ChemistryCrossEncoderReranker(BaseReranker):
    """
    Domain-Specific Chemistry Cross-Encoder Reranker.
    Re-scores candidate chunks by combining semantic query-text term overlap with chemical formula
    boosts, section header alignment, and LaTeX equation weightings.
    """

    async def rerank(self, request: RerankRequest) -> RerankResponse:
        query_text = request.query_text
        candidates = request.candidate_chunks

        if not candidates:
            return RerankResponse(query_text=query_text, results=[], total_reranked=0)

        logger.info(f"Reranking {len(candidates)} candidate evidence chunks for query '{query_text[:50]}...'")
        
        q_tokens = set(tokenize_chemistry_text(query_text))
        reranked_items: List[RerankedChunk] = []

        for candidate in candidates:
            # 1. Base term overlap score (Jaccard similarity approximation)
            c_tokens = set(tokenize_chemistry_text(candidate.text))
            intersection = q_tokens.intersection(c_tokens)
            union = q_tokens.union(c_tokens)
            overlap_score = len(intersection) / len(union) if union else 0.0

            # Blend base score with original similarity score
            base_score = 0.5 * candidate.score + 0.5 * overlap_score

            # 2. Chemical Formula Match Boost (+0.20)
            chem_boost = 0.0
            if candidate.chemical_entities:
                req_chem = {c.upper() for c in q_tokens if c.isupper()}
                chunk_chem = {c.upper() for c in candidate.chemical_entities}
                if req_chem and req_chem.intersection(chunk_chem):
                    chem_boost = 0.20
                elif candidate.chemical_entities:
                    chem_boost = 0.05

            # 3. Section Title Boost (+0.15)
            section_boost = 0.0
            if candidate.section_title:
                sec_lower = candidate.section_title.lower()
                if any(sec in sec_lower for sec in ACTIONABLE_SECTIONS):
                    section_boost = 0.15

            # 4. Equation / Math Boost (+0.10)
            equation_boost = 0.0
            if candidate.chunk_type == "equation" or "\\begin{equation}" in candidate.text:
                if any(k in query_text.lower() for k in ["equation", "formula", "delta", "kinetics", "rate", "energy"]):
                    equation_boost = 0.10

            # Calculate final normalized rerank score [0.0, 1.0]
            raw_rerank_score = base_score + chem_boost + section_boost + equation_boost
            final_rerank_score = min(1.0, max(0.0, raw_rerank_score))

            if final_rerank_score >= request.min_relevance_score:
                item = RerankedChunk(
                    chunk_id=candidate.chunk_id,
                    rerank_score=float(round(final_rerank_score, 4)),
                    original_score=float(candidate.score),
                    text=candidate.text,
                    document_id=candidate.document_id,
                    workspace_id=candidate.workspace_id,
                    page_number=candidate.page_number,
                    page_start=candidate.page_start,
                    page_end=candidate.page_end,
                    section_title=candidate.section_title,
                    chemical_entities=candidate.chemical_entities,
                    chunk_type=candidate.chunk_type,
                    payload=candidate.payload
                )
                reranked_items.append(item)

        # Sort descending by rerank_score
        reranked_items.sort(key=lambda x: x.rerank_score, reverse=True)
        final_results = reranked_items[:request.top_k]

        logger.info(f"Reranking completed returning top {len(final_results)} re-scored chunks.")

        return RerankResponse(
            query_text=query_text,
            results=final_results,
            total_reranked=len(final_results)
        )
