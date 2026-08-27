from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from ai.schemas.citation import Citation

class QuizType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"

class QuizOption(BaseModel):
    option_letter: str = Field(..., description="Option label e.g. 'A', 'B', 'C', 'D'")
    option_text: str = Field(..., description="Text of the choice option")
    is_correct: bool = Field(default=False, description="True if this choice is correct")

class QuizQuestion(BaseModel):
    question_id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., description="Question prompt text")
    question_type: QuizType = Field(default=QuizType.MULTIPLE_CHOICE, description="Type of quiz question")
    options: List[QuizOption] = Field(default_factory=list, description="Choice options for multiple choice questions")
    correct_answer: str = Field(..., description="Correct answer text or option letter")
    explanation: str = Field(..., description="Scientific explanation grounded in source paper")
    citations: List[Citation] = Field(default_factory=list, description="Source citations backing the question and answer")

class QuizGenerationRequest(BaseModel):
    workspace_id: str = Field(..., description="Workspace ID")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional list of document IDs to generate quiz from")
    num_questions: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")
    quiz_type: QuizType = Field(default=QuizType.MULTIPLE_CHOICE, description="Quiz question type")
    topic: Optional[str] = Field(default="Chemistry Literature", description="Optional topic focus")
    collection_name: str = Field(default="chem_papers", description="Vector store collection name")

class QuizResponse(BaseModel):
    quiz_id: str = Field(..., description="Unique quiz ID")
    title: str = Field(..., description="Quiz title")
    questions: List[QuizQuestion] = Field(default_factory=list, description="Generated quiz questions")
    workspace_id: str = Field(..., description="Workspace ID")
