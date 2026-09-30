"""
Summary request/response schemas.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class SummarySection(str, Enum):
    definition = "definition"
    key_concepts = "key_concepts"
    important_facts = "important_facts"
    formula_sheet = "formula_sheet"
    mnemonics = "mnemonics"
    exam_tips = "exam_tips"
    revision_notes = "revision_notes"
    checklist = "checklist"


class GenerateSummaryRequest(BaseModel):
    """Request body for topic-based summary generation."""
    topic: str = Field(..., min_length=2, max_length=500, description="Topic to summarize")
    sections: List[SummarySection] = Field(
        default=[
            SummarySection.definition,
            SummarySection.key_concepts,
            SummarySection.important_facts,
            SummarySection.revision_notes,
        ],
        description="Which sections to include in the summary",
    )
    model: Optional[str] = Field(None, description="AI model ID (e.g. 'openai/gpt-oss-120b')")
    provider: Optional[str] = Field(None, description="AI provider name (e.g. 'groq', 'openai', 'google')")


class GenerateSummaryFromFileRequest(BaseModel):
    """Request body for file-based summary generation."""
    upload_id: uuid.UUID = Field(..., description="ID of a previously uploaded file")
    sections: List[SummarySection] = Field(
        default=[
            SummarySection.key_concepts,
            SummarySection.important_facts,
            SummarySection.revision_notes,
        ],
    )
    model: Optional[str] = None
    provider: Optional[str] = None


class SummaryResponse(BaseModel):
    """Full summary response."""
    id: uuid.UUID
    topic: str
    sections_requested: List[str]
    content: Dict[str, str]  # section_name -> content
    model_used: str
    is_from_file: bool
    word_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class SummaryListItem(BaseModel):
    """Lightweight summary for list views."""
    id: uuid.UUID
    topic: str
    sections_requested: List[str]
    is_from_file: bool
    created_at: datetime

    model_config = {"from_attributes": True}
