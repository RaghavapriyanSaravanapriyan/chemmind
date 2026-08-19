from typing import Dict, List, Tuple
from ai.schemas.retrieval import RetrievedChunk
from ai.utils.logger import logger

def reciprocal_rank_fusion(
    dense_results: List[RetrievedChunk],
    sparse_results: List[RetrievedChunk],
    k: int = 60
) -> List[RetrievedChunk]:
    """
    Fuses dense vector and sparse keyword retrieval rankings using Reciprocal Rank Fusion (RRF).
    
    Formula: RRF_score(chunk) = 1/(k + dense_rank) + 1/(k + sparse_rank)
    """
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, RetrievedChunk] = {}

    # Accumulate dense ranks
    for rank, chunk in enumerate(dense_results, start=1):
        c_id = chunk.chunk_id
        chunk_map[c_id] = chunk
        rrf_score = 1.0 / (k + rank)
        scores[c_id] = scores.get(c_id, 0.0) + rrf_score

    # Accumulate sparse ranks
    for rank, chunk in enumerate(sparse_results, start=1):
        c_id = chunk.chunk_id
        if c_id not in chunk_map:
            chunk_map[c_id] = chunk
        rrf_score = 1.0 / (k + rank)
        scores[c_id] = scores.get(c_id, 0.0) + rrf_score

    # Sort candidates by combined RRF score descending
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    fused_results: List[RetrievedChunk] = []
    for c_id, score in sorted_items:
        orig_chunk = chunk_map[c_id]
        # Return new RetrievedChunk instance with combined RRF score
        fused_chunk = RetrievedChunk(
            chunk_id=orig_chunk.chunk_id,
            score=float(score),
            text=orig_chunk.text,
            document_id=orig_chunk.document_id,
            workspace_id=orig_chunk.workspace_id,
            page_number=orig_chunk.page_number,
            page_start=orig_chunk.page_start,
            page_end=orig_chunk.page_end,
            section_title=orig_chunk.section_title,
            chemical_entities=orig_chunk.chemical_entities,
            chunk_type=orig_chunk.chunk_type,
            payload=orig_chunk.payload
        )
        fused_results.append(fused_chunk)

    logger.info(f"RRF fused {len(dense_results)} dense and {len(sparse_results)} sparse candidates into {len(fused_results)} unified results.")
    return fused_results
