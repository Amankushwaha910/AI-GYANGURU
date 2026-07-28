"""
SQLAlchemy ORM models — all imported here so Alembic can discover them.
Order matters: parent tables must be imported before child tables.
"""
from app.models.user import User, Profile          # noqa: F401
from app.models.upload import Upload               # noqa: F401
from app.models.summary import Summary             # noqa: F401
from app.models.explanation import Explanation     # noqa: F401
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer  # noqa: F401
from app.models.analytics import AnalyticsEvent   # noqa: F401
from app.models.history import HistoryItem         # noqa: F401
from app.models.ai_log import AIRequest, AIResponse  # noqa: F401

__all__ = [
    "User",
    "Profile",
    "Upload",
    "Summary",
    "Explanation",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "QuizAnswer",
    "AnalyticsEvent",
    "HistoryItem",
    "AIRequest",
    "AIResponse",
]
