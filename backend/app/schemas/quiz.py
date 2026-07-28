"""
Quiz request/response schemas.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.quiz import QuizDifficulty


class GenerateQuizRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    question_count: int = Field(default=10, ge=5, le=20, description="Number of questions (5–20)")
    difficulty: QuizDifficulty = Field(default=QuizDifficulty.mixed)
    category: Optional[str] = Field(None, max_length=200)
    model: Optional[str] = None


class GenerateQuizFromFileRequest(BaseModel):
    upload_id: uuid.UUID
    question_count: int = Field(default=10, ge=5, le=20)
    difficulty: QuizDifficulty = Field(default=QuizDifficulty.mixed)
    category: Optional[str] = Field(None, max_length=200)
    model: Optional[str] = None


class QuizQuestionResponse(BaseModel):
    id: uuid.UUID
    order_index: int
    question_text: str
    options: List[str]  # ["A. ...", "B. ...", "C. ...", "D. ..."]
    difficulty: str
    category: Optional[str] = None
    # NOTE: correct_option and explanation are NOT returned during the quiz
    # They are only returned after submission

    model_config = {"from_attributes": True}


class QuizQuestionWithAnswerResponse(QuizQuestionResponse):
    """Extended response that includes correct answer — returned after submission."""
    correct_option: str
    explanation: str


class QuizResponse(BaseModel):
    id: uuid.UUID
    topic: str
    difficulty: QuizDifficulty
    category: Optional[str] = None
    question_count: int
    model_used: str
    is_from_file: bool
    questions: List[QuizQuestionResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class SubmitAnswerItem(BaseModel):
    question_id: uuid.UUID = Field(..., description="Quiz question ID")
    selected_option: Optional[str] = Field(None, description="Selected option: A, B, C, or D")

    @field_validator("selected_option")
    @classmethod
    def validate_option(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in ("A", "B", "C", "D"):
            raise ValueError("selected_option must be A, B, C, or D")
        return v.upper() if v else None


class SubmitQuizRequest(BaseModel):
    answers: List[SubmitAnswerItem] = Field(..., description="List of answers for each question")
    time_taken_seconds: Optional[int] = Field(None, description="Total time taken in seconds")


class QuizResultQuestionItem(BaseModel):
    question_id: uuid.UUID
    question_text: str
    options: List[str]
    selected_option: Optional[str]
    correct_option: str
    is_correct: bool
    explanation: str


class QuizAttemptResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    topic: str
    score: int
    total_questions: int
    percentage: float
    correct_count: int
    wrong_count: int
    time_taken_seconds: Optional[int] = None
    performance_summary: Optional[str] = None
    questions: List[QuizResultQuestionItem]
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizListItem(BaseModel):
    id: uuid.UUID
    topic: str
    difficulty: QuizDifficulty
    question_count: int
    is_from_file: bool
    created_at: datetime
    latest_score: Optional[float] = None

    model_config = {"from_attributes": True}
