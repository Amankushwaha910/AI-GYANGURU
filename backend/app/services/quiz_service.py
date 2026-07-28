"""
Quiz service — generation, submission, scoring, and persistence.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.dispatcher import get_dispatcher
from app.ai.prompt_builder import get_prompt_builder
from app.ai.response_formatter import get_response_formatter
from app.core.exceptions import NotFoundError, ValidationError
from app.models.analytics import EventType
from app.models.history import HistoryItemType
from app.models.quiz import Quiz, QuizAnswer, QuizAttempt, QuizDifficulty, QuizQuestion
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.quiz_repository import QuizAttemptRepository, QuizRepository
from app.repositories.upload_repository import UploadRepository
from app.schemas.quiz import (
    GenerateQuizFromFileRequest,
    GenerateQuizRequest,
    QuizAttemptResponse,
    QuizResultQuestionItem,
    SubmitQuizRequest,
)


class QuizService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.quiz_repo = QuizRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)
        self.upload_repo = UploadRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        self.history_repo = HistoryRepository(db)
        self.dispatcher = get_dispatcher()
        self.prompt_builder = get_prompt_builder()
        self.formatter = get_response_formatter()

    async def generate_from_topic(
        self, user_id: UUID, request: GenerateQuizRequest
    ) -> Quiz:
        messages = self.prompt_builder.build_quiz_prompt(
            topic=request.topic,
            question_count=request.question_count,
            difficulty=request.difficulty.value,
            category=request.category,
        )

        ai_response, _ = await self.dispatcher.complete(
            messages=messages,
            model=request.model,
            temperature=0.5,  # Lower temp for factual accuracy
        )

        parsed = self.formatter.extract_json(ai_response.content)
        questions_data = self.formatter.validate_quiz_response(parsed)

        return await self._persist_quiz(
            user_id=user_id,
            topic=request.topic,
            difficulty=request.difficulty,
            category=request.category,
            model_used=ai_response.model,
            questions_data=questions_data,
            is_from_file=False,
        )

    async def generate_from_file(
        self, user_id: UUID, request: GenerateQuizFromFileRequest
    ) -> Quiz:
        upload = await self.upload_repo.get_user_upload(user_id, request.upload_id)
        if not upload or not upload.extracted_text:
            raise NotFoundError("Upload or extracted text", str(request.upload_id))

        topic = f"Content from: {upload.original_filename}"
        messages = self.prompt_builder.build_quiz_prompt(
            topic=topic,
            question_count=request.question_count,
            difficulty=request.difficulty.value,
            category=request.category,
            extracted_text=upload.extracted_text,
        )

        ai_response, _ = await self.dispatcher.complete(
            messages=messages, model=request.model, temperature=0.5
        )

        parsed = self.formatter.extract_json(ai_response.content)
        questions_data = self.formatter.validate_quiz_response(parsed)

        return await self._persist_quiz(
            user_id=user_id,
            topic=topic,
            difficulty=request.difficulty,
            category=request.category,
            model_used=ai_response.model,
            questions_data=questions_data,
            is_from_file=True,
            upload_id=request.upload_id,
        )

    async def get_quiz(self, user_id: UUID, quiz_id: UUID) -> Quiz:
        quiz = await self.quiz_repo.get_with_questions(quiz_id)
        if not quiz or quiz.user_id != user_id:
            raise NotFoundError("Quiz", str(quiz_id))
        return quiz

    async def list_quizzes(
        self, user_id: UUID, page: int, page_size: int, search: Optional[str]
    ) -> Tuple[List[Quiz], int]:
        return await self.quiz_repo.get_user_quizzes(
            user_id=user_id, page=page, page_size=page_size, search=search
        )

    async def submit_quiz(
        self, user_id: UUID, quiz_id: UUID, request: SubmitQuizRequest
    ) -> QuizAttemptResponse:
        """Score a quiz attempt and persist results."""
        quiz = await self.quiz_repo.get_with_questions(quiz_id)
        if not quiz or quiz.user_id != user_id:
            raise NotFoundError("Quiz", str(quiz_id))

        if len(request.answers) == 0:
            raise ValidationError("At least one answer must be provided")

        # Build a lookup: question_id -> QuizQuestion
        question_map = {str(q.id): q for q in quiz.questions}

        # Score the attempt
        correct_count = 0
        answer_records = []
        result_items: List[QuizResultQuestionItem] = []

        for answer_item in request.answers:
            q = question_map.get(str(answer_item.question_id))
            if not q:
                continue

            is_correct = (
                answer_item.selected_option is not None
                and answer_item.selected_option.upper() == q.correct_option.upper()
            )
            if is_correct:
                correct_count += 1

            answer_records.append({
                "question_id": q.id,
                "selected_option": answer_item.selected_option,
                "is_correct": is_correct,
            })

            result_items.append(
                QuizResultQuestionItem(
                    question_id=q.id,
                    question_text=q.question_text,
                    options=q.options,
                    selected_option=answer_item.selected_option,
                    correct_option=q.correct_option,
                    is_correct=is_correct,
                    explanation=q.explanation,
                )
            )

        total = len(quiz.questions)
        percentage = round((correct_count / total) * 100, 1) if total > 0 else 0.0

        # Generate AI performance summary
        wrong_cats = list({
            r.category for r in quiz.questions
            if str(r.id) in [str(a["question_id"]) for a in answer_records
                              if not a["is_correct"]] and r.category
        })
        correct_cats = list({
            r.category for r in quiz.questions
            if str(r.id) in [str(a["question_id"]) for a in answer_records
                              if a["is_correct"]] and r.category
        })

        perf_messages = self.prompt_builder.build_performance_summary_prompt(
            topic=quiz.topic,
            score=correct_count,
            total=total,
            wrong_categories=wrong_cats,
            correct_categories=correct_cats,
        )
        try:
            perf_response, _ = await self.dispatcher.complete(
                messages=perf_messages, temperature=0.6
            )
            performance_summary = perf_response.content.strip()
        except Exception:
            performance_summary = f"You scored {correct_count}/{total} ({percentage}%)."

        # Persist attempt
        attempt = await self.attempt_repo.create(
            quiz_id=quiz_id,
            user_id=user_id,
            score=correct_count,
            total_questions=total,
            percentage=percentage,
            time_taken_seconds=request.time_taken_seconds,
            performance_summary=performance_summary,
        )

        # Persist individual answers
        for ar in answer_records:
            answer = QuizAnswer(
                attempt_id=attempt.id,
                question_id=ar["question_id"],
                selected_option=ar["selected_option"],
                is_correct=ar["is_correct"],
            )
            self.db.add(answer)
        await self.db.flush()

        # Analytics + history
        await self.analytics_repo.log_event(
            user_id=user_id,
            event_type=EventType.quiz_completed,
            topic=quiz.topic,
            module="quiz",
            resource_id=str(attempt.id),
        )
        await self.history_repo.add_entry(
            user_id=user_id,
            item_type=HistoryItemType.quiz,
            topic=quiz.topic,
            resource_id=str(attempt.id),
        )

        return QuizAttemptResponse(
            id=attempt.id,
            quiz_id=quiz_id,
            topic=quiz.topic,
            score=correct_count,
            total_questions=total,
            percentage=percentage,
            correct_count=correct_count,
            wrong_count=total - correct_count,
            time_taken_seconds=request.time_taken_seconds,
            performance_summary=performance_summary,
            questions=result_items,
            created_at=attempt.created_at,
        )

    async def get_attempt(self, user_id: UUID, attempt_id: UUID) -> QuizAttempt:
        attempt = await self.attempt_repo.get_with_answers(attempt_id)
        if not attempt or attempt.user_id != user_id:
            raise NotFoundError("Quiz attempt", str(attempt_id))
        return attempt

    async def _persist_quiz(
        self,
        user_id: UUID,
        topic: str,
        difficulty: QuizDifficulty,
        category: Optional[str],
        model_used: str,
        questions_data: List[dict],
        is_from_file: bool,
        upload_id: Optional[UUID] = None,
    ) -> Quiz:
        quiz = await self.quiz_repo.create(
            user_id=user_id,
            upload_id=upload_id,
            topic=topic,
            difficulty=difficulty,
            category=category,
            question_count=len(questions_data),
            model_used=model_used,
            is_from_file=is_from_file,
        )

        for idx, q_data in enumerate(questions_data):
            question = QuizQuestion(
                quiz_id=quiz.id,
                order_index=idx,
                question_text=q_data["question_text"],
                options=q_data["options"],
                correct_option=q_data["correct_option"],
                explanation=q_data["explanation"],
                difficulty=q_data["difficulty"],
                category=q_data.get("category"),
            )
            self.db.add(question)

        await self.db.flush()
        await self.db.refresh(quiz)

        await self.analytics_repo.log_event(
            user_id=user_id,
            event_type=EventType.quiz_generated,
            topic=topic,
            module="quiz",
            resource_id=str(quiz.id),
        )

        return quiz
