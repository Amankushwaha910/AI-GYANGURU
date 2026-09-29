"""
Quiz routes — /api/v1/quizzes
"""
import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, CurrentUserFast
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.quiz import (
    GenerateQuizFromFileRequest,
    GenerateQuizRequest,
    QuizAttemptResponse,
    QuizListItem,
    QuizResponse,
    QuizQuestionResponse,
    SubmitQuizRequest,
)
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("", response_model=APIResponse[QuizResponse], status_code=201)
async def generate_quiz(
    request: GenerateQuizRequest,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Generate a quiz for a topic using AI."""
    service = QuizService(db)
    quiz = await service.generate_from_topic(current_user.id, request)
    # Reload with questions eager-loaded
    quiz = await service.get_quiz(current_user.id, quiz.id)

    questions = [
        QuizQuestionResponse(
            id=q.id,
            order_index=q.order_index,
            question_text=q.question_text,
            options=q.options,
            difficulty=q.difficulty,
            category=q.category,
        )
        for q in sorted(quiz.questions, key=lambda x: x.order_index)
    ]

    return APIResponse(
        data=QuizResponse(
            id=quiz.id,
            topic=quiz.topic,
            difficulty=quiz.difficulty,
            category=quiz.category,
            question_count=quiz.question_count,
            model_used=quiz.model_used,
            is_from_file=quiz.is_from_file,
            questions=questions,
            created_at=quiz.created_at,
        ),
        message="Quiz generated successfully",
    )


@router.post("/from-file", response_model=APIResponse[QuizResponse], status_code=201)
async def generate_quiz_from_file(
    request: GenerateQuizFromFileRequest,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Generate a quiz from a previously uploaded file."""
    service = QuizService(db)
    quiz = await service.generate_from_file(current_user.id, request)
    quiz = await service.get_quiz(current_user.id, quiz.id)

    questions = [
        QuizQuestionResponse(
            id=q.id,
            order_index=q.order_index,
            question_text=q.question_text,
            options=q.options,
            difficulty=q.difficulty,
            category=q.category,
        )
        for q in sorted(quiz.questions, key=lambda x: x.order_index)
    ]

    return APIResponse(
        data=QuizResponse(
            id=quiz.id,
            topic=quiz.topic,
            difficulty=quiz.difficulty,
            category=quiz.category,
            question_count=quiz.question_count,
            model_used=quiz.model_used,
            is_from_file=quiz.is_from_file,
            questions=questions,
            created_at=quiz.created_at,
        ),
        message="Quiz generated from file",
    )


@router.get("", response_model=PaginatedResponse[QuizListItem])
async def list_quizzes(
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
):
    """List the current user's quizzes."""
    service = QuizService(db)
    quizzes, total = await service.list_quizzes(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
    )
    return PaginatedResponse(
        data=[QuizListItem.model_validate(q) for q in quizzes],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.get("/{quiz_id}", response_model=APIResponse[QuizResponse])
async def get_quiz(
    quiz_id: UUID,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific quiz with questions (answers hidden)."""
    service = QuizService(db)
    quiz = await service.get_quiz(current_user.id, quiz_id)

    questions = [
        QuizQuestionResponse(
            id=q.id,
            order_index=q.order_index,
            question_text=q.question_text,
            options=q.options,
            difficulty=q.difficulty,
            category=q.category,
        )
        for q in sorted(quiz.questions, key=lambda x: x.order_index)
    ]

    return APIResponse(
        data=QuizResponse(
            id=quiz.id,
            topic=quiz.topic,
            difficulty=quiz.difficulty,
            category=quiz.category,
            question_count=quiz.question_count,
            model_used=quiz.model_used,
            is_from_file=quiz.is_from_file,
            questions=questions,
            created_at=quiz.created_at,
        )
    )


@router.post("/{quiz_id}/submit", response_model=APIResponse[QuizAttemptResponse])
async def submit_quiz(
    quiz_id: UUID,
    request: SubmitQuizRequest,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Submit quiz answers and receive scored results with explanations."""
    service = QuizService(db)
    result = await service.submit_quiz(current_user.id, quiz_id, request)
    return APIResponse(data=result, message="Quiz submitted successfully")


@router.get("/{quiz_id}/attempts/{attempt_id}", response_model=APIResponse[QuizAttemptResponse])
async def get_attempt(
    quiz_id: UUID,
    attempt_id: UUID,
    current_user: CurrentUserFast,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a past quiz attempt with full question review."""
    service = QuizService(db)
    attempt = await service.get_attempt(current_user.id, attempt_id)

    from app.schemas.quiz import QuizResultQuestionItem
    result_items = [
        QuizResultQuestionItem(
            question_id=a.question.id,
            question_text=a.question.question_text,
            options=a.question.options,
            selected_option=a.selected_option,
            correct_option=a.question.correct_option,
            is_correct=a.is_correct,
            explanation=a.question.explanation,
        )
        for a in attempt.answers
    ]

    return APIResponse(
        data=QuizAttemptResponse(
            id=attempt.id,
            quiz_id=quiz_id,
            topic=attempt.quiz.topic if attempt.quiz else "",
            score=attempt.score,
            total_questions=attempt.total_questions,
            percentage=attempt.percentage,
            correct_count=attempt.score,
            wrong_count=attempt.total_questions - attempt.score,
            time_taken_seconds=attempt.time_taken_seconds,
            performance_summary=attempt.performance_summary,
            questions=result_items,
            created_at=attempt.created_at,
        )
    )
