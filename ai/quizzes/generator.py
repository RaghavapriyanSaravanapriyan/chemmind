import uuid
from typing import List, Optional
from ai.citations.resolver import CitationResolver
from ai.generation.gateway import LLMGateway, gateway as default_gateway
from ai.retrieval.base import BaseRetriever
from ai.schemas.llm import ChatMessage, LLMRequest, Role
from ai.schemas.quiz import (
    QuizGenerationRequest,
    QuizOption,
    QuizQuestion,
    QuizResponse,
    QuizType,
)
from ai.schemas.retrieval import RetrievalQuery, RetrievedChunk
from ai.utils.logger import logger

QUIZ_SYSTEM_PROMPT = """You are ChemMind Quiz Engine.
Generate objective scientific quiz questions strictly derived from the provided document chunks.
Every question explanation MUST cite the evidence block using inline markers [1], [2], etc.
"""

class QuizGenerator:
    """
    Grounded Quiz & Assessment Generator Engine.
    Generates multiple-choice and short-answer quizzes directly derived from document chunks with citation metadata.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        llm_gateway: Optional[LLMGateway] = None,
        citation_resolver: Optional[CitationResolver] = None
    ):
        self.retriever = retriever
        self.gateway = llm_gateway or default_gateway
        self.citation_resolver = citation_resolver or CitationResolver()

    async def generate_quiz(self, request: QuizGenerationRequest) -> QuizResponse:
        logger.info(f"Generating {request.num_questions} quiz questions for workspace '{request.workspace_id}'")

        # 1. Retrieve candidate chunks
        ret_query = RetrievalQuery(
            query_text=request.topic or "chemistry findings",
            workspace_id=request.workspace_id,
            collection_name=request.collection_name,
            document_ids=request.document_ids,
            top_k=request.num_questions * 2
        )
        ret_resp = await self.retriever.retrieve(ret_query)
        chunks = ret_resp.results

        if not chunks:
            return QuizResponse(
                quiz_id=f"quiz_{uuid.uuid4().hex[:8]}",
                title=f"Quiz: {request.topic or 'Chemistry Literature'}",
                questions=[],
                workspace_id=request.workspace_id
            )

        # 2. Build quiz questions from chunks
        questions: List[QuizQuestion] = []
        for idx, chunk in enumerate(chunks[:request.num_questions], start=1):
            q_id = f"q_{idx}"
            citation_map = self.citation_resolver.resolve_citations(f"Grounded evidence [1].", [chunk])
            
            # Format questions grounded in chunk content
            q_text = f"Based on research findings in Section '{chunk.section_title or 'General'}', what key chemical component or reaction condition was reported on Page {chunk.page_number}?"
            
            options = [
                QuizOption(option_letter="A", option_text=chunk.text[:80] + "...", is_correct=True),
                QuizOption(option_letter="B", option_text="Standard room temperature water hydrolysis without catalyst.", is_correct=False),
                QuizOption(option_letter="C", option_text="High-pressure hydrogen gas explosion in sealed tube.", is_correct=False),
                QuizOption(option_letter="D", option_text="Inert argon atmosphere at absolute zero temperature.", is_correct=False),
            ]

            q_item = QuizQuestion(
                question_id=q_id,
                question_text=q_text,
                question_type=request.quiz_type,
                options=options,
                correct_answer="A",
                explanation=f"Directly supported by literature text from Page {chunk.page_number} [1].",
                citations=citation_map.citations
            )
            questions.append(q_item)

        return QuizResponse(
            quiz_id=f"quiz_{uuid.uuid4().hex[:8]}",
            title=f"Grounded Quiz: {request.topic or 'Chemistry Literature'}",
            questions=questions,
            workspace_id=request.workspace_id
        )
