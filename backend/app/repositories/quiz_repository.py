"""
Quiz repository — quiz, questions, and attempts.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz, QuizAnswer, QuizAttempt, QuizQuestion
from app.repositories.base_repository import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Quiz, db)

    async def get_with_questions(self, quiz_id: UUID) -> Optional[Quiz]:
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.id == quiz_id)
            .options(selectinload(Quiz.questions))
        )
        return result.scalar_one_or_none()

    async def get_user_quizzes(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[Quiz], int]:
        query = select(Quiz).where(Quiz.user_id == user_id)
        if search:
            query = query.where(Quiz.topic.ilike(f"%{search}%"))

        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar_one()

        query = query.order_by(Quiz.created_at.desc())
        query = query.limit(page_size).offset((page - 1) * page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def count_for_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(Quiz.user_id == user_id)
        )
        return result.scalar_one()


class QuizAttemptRepository(BaseRepository[QuizAttempt]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(QuizAttempt, db)

    async def get_with_answers(self, attempt_id: UUID) -> Optional[QuizAttempt]:
        result = await self.db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.id == attempt_id)
            .options(
                selectinload(QuizAttempt.quiz),
                selectinload(QuizAttempt.answers).selectinload(QuizAnswer.question)
            )
        )
        return result.scalar_one_or_none()

    async def get_user_attempts(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[QuizAttempt], int]:
        query = select(QuizAttempt).where(QuizAttempt.user_id == user_id)
        total = (
            await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar_one()

        query = query.order_by(QuizAttempt.created_at.desc())
        query = query.limit(page_size).offset((page - 1) * page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_accuracy_by_category(
        self, user_id: UUID
    ) -> List[dict]:
        """Return per-category accuracy stats for analytics."""
        # Raw aggregation — uses SQLAlchemy Core for complex query
        from sqlalchemy import case, cast, Float
        from app.models.quiz import Quiz

        result = await self.db.execute(
            select(
                QuizQuestion.category,
                func.count(QuizAnswer.id).label("total"),
                func.sum(
                    case((QuizAnswer.is_correct == True, 1), else_=0)
                ).label("correct"),
            )
            .join(QuizAnswer, QuizAnswer.question_id == QuizQuestion.id)
            .join(QuizAttempt, QuizAttempt.id == QuizAnswer.attempt_id)
            .where(QuizAttempt.user_id == user_id)
            .where(QuizQuestion.category.isnot(None))
            .group_by(QuizQuestion.category)
        )
        rows = result.all()
        return [
            {
                "category": row.category,
                "total": row.total,
                "correct": int(row.correct or 0),
                "accuracy": round((int(row.correct or 0) / row.total) * 100, 1),
            }
            for row in rows
        ]
