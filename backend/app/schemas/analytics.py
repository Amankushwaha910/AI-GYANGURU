"""
Analytics response schemas.
"""
from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DailyActivityItem(BaseModel):
    date: date
    count: float  # int for activity counts, float for accuracy percentages


class CategoryAccuracy(BaseModel):
    category: str
    accuracy: float
    attempt_count: int


class AnalyticsSummary(BaseModel):
    """Top-level analytics summary stats."""
    total_topics_studied: int = Field(..., description="Unique topics studied all-time")
    total_summaries_generated: int
    total_explanations_generated: int
    total_quizzes_taken: int
    overall_quiz_accuracy: float = Field(..., description="Percentage (0–100)")


class AnalyticsDashboard(BaseModel):
    """Full analytics dashboard data."""
    summary: AnalyticsSummary
    daily_activity: List[DailyActivityItem] = Field(
        ..., description="Topics studied per day, last 30 days"
    )
    quiz_accuracy_trend: List[DailyActivityItem] = Field(
        ..., description="Average quiz accuracy per day, last 30 days"
    )
    activity_heatmap: List[DailyActivityItem] = Field(
        ..., description="All activity per day, last 90 days"
    )
    weak_areas: List[CategoryAccuracy] = Field(
        ..., description="Categories with lowest quiz accuracy"
    )
    strong_areas: List[CategoryAccuracy] = Field(
        ..., description="Categories with highest quiz accuracy"
    )


class HistoryTimelineItem(BaseModel):
    id: str
    item_type: str
    topic: str
    created_at: str
