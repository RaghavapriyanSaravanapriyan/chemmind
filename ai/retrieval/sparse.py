import math
import re
from typing import Dict, List, Optional
from ai.schemas.document import DocumentChunk
from ai.schemas.retrieval import RetrievalQuery, RetrievedChunk
from ai.utils.logger import logger

def tokenize_chemistry_text(text: str) -> List[str]:
    """
    Tokenizes text while preserving chemical formulas, SMILES, and LaTeX environment tokens.
    """
    tokens = re.findall(r"\\[a-zA-Z]+|[A-Za-z0-9_\-\(\)\+\=]+", text)
    processed = []
    for tok in tokens:
        # Preserve formulas containing digits or uppercase letters intact, lowercase standard words
        if any(c.isdigit() for c in tok) or (tok.isupper() and len(tok) <= 8):
            processed.append(tok)
        else:
            processed.append(tok.lower())
    return processed

class BM25KeywordRetriever:
    """
    Sparse BM25 Keyword Retriever over DocumentChunks.
    Supports in-memory index building or dynamic collection ranking for keyword retrieval.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def rank_chunks(self, query_text: str, chunks: List[DocumentChunk], top_k: int = 10) -> List[RetrievedChunk]:
        """Ranks a list of DocumentChunks against query_text using BM25 scoring."""
        if not chunks or not query_text:
            return []

        query_tokens = tokenize_chemistry_text(query_text)
        if not query_tokens:
            return []

        doc_count = len(chunks)
        doc_tokens_list = [tokenize_chemistry_text(c.text) for c in chunks]
        doc_lens = [len(dt) for dt in doc_tokens_list]
        avgdl = sum(doc_lens) / doc_count if doc_count > 0 else 1.0

        # Calculate Document Frequency (DF) for query tokens
        df: Dict[str, int] = {}
        for q_tok in set(query_tokens):
            df[q_tok] = sum(1 for dt in doc_tokens_list if q_tok in dt)

        # Compute BM25 scores
        scored_results: List[RetrievedChunk] = []
        for chunk, doc_toks, doc_len in zip(chunks, doc_tokens_list, doc_lens):
            score = 0.0
            # Term frequencies in this document
            tf: Dict[str, int] = {}
            for tok in doc_toks:
                tf[tok] = tf.get(tok, 0) + 1

            for q_tok in query_tokens:
                if q_tok not in tf:
                    continue
                q_df = df.get(q_tok, 0)
                # IDF calculation with smoothing
                idf = math.log((doc_count - q_df + 0.5) / (q_df + 0.5) + 1.0)
                
                term_tf = tf[q_tok]
                numerator = term_tf * (self.k1 + 1.0)
                denominator = term_tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                score += idf * (numerator / denominator)

            if score > 0.0:
                retrieved_item = RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    score=float(score),
                    text=chunk.text,
                    document_id=chunk.document_id,
                    workspace_id=chunk.workspace_id,
                    page_number=chunk.page_number,
                    page_start=chunk.page_start or chunk.page_number,
                    page_end=chunk.page_end or chunk.page_number,
                    section_title=chunk.section_title,
                    chemical_entities=chunk.chemical_entities,
                    chunk_type=chunk.chunk_type
                )
                scored_results.append(retrieved_item)

        # Sort descending by BM25 score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:top_k]
