"""
Explanation request/response schemas.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GenerateExplanationRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Concept to explain")
    model: Optional[str] = Field(None, description="AI model to use")


class GenerateExplanationFromFileRequest(BaseModel):
    upload_id: uuid.UUID = Field(..., description="ID of a previously uploaded file")
    model: Optional[str] = None


class ExplanationContent(BaseModel):
    """Structured explanation sections."""
    introduction: str = ""
    step_by_step: str = ""
    concept_breakdown: str = ""
    real_examples: str = ""
    analogies: str = ""
    practical_applications: str = ""
    common_mistakes: str = ""
    faqs: str = ""
    final_recap: str = ""


class ExplanationResponse(BaseModel):
    id: uuid.UUID
    topic: str
    content: Dict[str, str]
    model_used: str
    is_from_file: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ExplanationListItem(BaseModel):
    id: uuid.UUID
    topic: str
    is_from_file: bool
    created_at: datetime

    model_config = {"from_attributes": True}
