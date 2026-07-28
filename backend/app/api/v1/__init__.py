from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    dashboard,
    explanations,
    files,
    history,
    quizzes,
    summaries,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(summaries.router)
api_router.include_router(explanations.router)
api_router.include_router(quizzes.router)
api_router.include_router(files.router)
api_router.include_router(analytics.router)
api_router.include_router(history.router)
