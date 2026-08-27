from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from ai.schemas.retrieval import RetrievedChunk
from ai.utils.logger import logger


class RoutingMode(str, Enum):
    INTERNAL_ONLY = "internal_only"
    HYBRID_AUGMENTED = "hybrid_augmented"
    WEB_FALLBACK = "web_fallback"


class RoutingDecision(BaseModel):
    mode: RoutingMode = Field(..., description="Chosen routing mode")
    should_use_web: bool = Field(..., description="Whether web search tool should be invoked")
    reason: str = Field(..., description="Explanation for routing decision")
    confidence: float = Field(..., description="Confidence level in decision (0.0 to 1.0)")


class AgenticRouter:
    """
    Intelligent Agentic Router that evaluates query scope, user intent,
    and internal document context sufficiency before invoking tools.
    """

    EXPLICIT_WEB_KEYWORDS = [
        "web", "internet", "google", "search the web", "latest", "recent",
        "current news", "online", "wikipedia", "pubmed", "2025", "2026", "outside docs"
    ]

    def __init__(self, sufficiency_threshold: float = 0.30):
        self.sufficiency_threshold = sufficiency_threshold

    def evaluate(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
        force_web: Optional[bool] = None,
    ) -> RoutingDecision:
        query_lower = query.lower()

        # 1. User forced override check
        if force_web is True:
            logger.info("AgenticRouter: Web search explicitly forced by request flag.")
            return RoutingDecision(
                mode=RoutingMode.WEB_FALLBACK if not retrieved_chunks else RoutingMode.HYBRID_AUGMENTED,
                should_use_web=True,
                reason="Web search explicitly requested.",
                confidence=1.0,
            )

        # 2. Check explicit internet/web keywords in query
        if any(kw in query_lower for kw in self.EXPLICIT_WEB_KEYWORDS):
            logger.info("AgenticRouter: Query contains explicit web research request keywords.")
            return RoutingDecision(
                mode=RoutingMode.HYBRID_AUGMENTED if retrieved_chunks else RoutingMode.WEB_FALLBACK,
                should_use_web=True,
                reason="Query contains explicit internet or scientific search keywords.",
                confidence=0.9,
            )

        # 3. Evaluate internal document retrieval results
        if not retrieved_chunks:
            logger.info("AgenticRouter: No internal document chunks retrieved. Triggering Web Fallback.")
            return RoutingDecision(
                mode=RoutingMode.WEB_FALLBACK,
                should_use_web=True,
                reason="No internal document chunks found in workspace vector store.",
                confidence=0.95,
            )

        # Calculate max and average similarity score among retrieved chunks
        scores = [chunk.score for chunk in retrieved_chunks if hasattr(chunk, "score")]
        max_score = max(scores) if scores else 0.0

        if max_score < self.sufficiency_threshold:
            logger.info(f"AgenticRouter: Max internal score {max_score:.3f} is below threshold {self.sufficiency_threshold}. Web search needed.")
            return RoutingDecision(
                mode=RoutingMode.WEB_FALLBACK,
                should_use_web=True,
                reason=f"Internal document evidence score ({max_score:.2f}) is below sufficiency threshold ({self.sufficiency_threshold:.2f}).",
                confidence=0.85,
            )

        # 4. Internal document context is sufficient
        logger.info(f"AgenticRouter: Internal document context sufficient (max_score: {max_score:.3f}). Web search bypassed.")
        return RoutingDecision(
            mode=RoutingMode.INTERNAL_ONLY,
            should_use_web=False,
            reason=f"Sufficient internal document evidence found (max similarity score: {max_score:.2f}).",
            confidence=0.92,
        )
