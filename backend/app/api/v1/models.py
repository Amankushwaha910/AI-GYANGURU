"""
Models endpoint — returns available AI providers and models.
GET /api/v1/models
"""
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.dispatcher import get_dispatcher
from app.core.config import settings
from app.schemas.common import APIResponse

router = APIRouter(prefix="/models", tags=["AI Models"])


class ModelInfo(BaseModel):
    id: str
    display_name: str
    provider: str
    provider_display_name: str
    description: str


class ModelsResponse(BaseModel):
    default_provider: str
    default_model: str
    providers: List[dict]


_PROVIDER_META = {
    "groq": {
        "display_name": "Groq",
        "description": "Ultra-fast inference via Groq LPU hardware",
    },
    "openai": {
        "display_name": "OpenAI",
        "description": "GPT models from OpenAI",
    },
    "google": {
        "display_name": "Google",
        "description": "Gemini models from Google DeepMind",
    },
}

_MODEL_META = {
    # Groq — Developer plan models (verified September 2026)
    "openai/gpt-oss-120b":     {"display_name": "GPT-OSS 120B",  "description": "OpenAI open-weight 120B on Groq — fast and capable"},
    "openai/gpt-oss-20b":      {"display_name": "GPT-OSS 20B",   "description": "OpenAI open-weight 20B on Groq — ultra-fast"},
    "qwen/qwen3.8-27b":        {"display_name": "Qwen 3.8 27B",  "description": "Alibaba Qwen multilingual model on Groq"},
    # OpenAI
    "gpt-4o":                  {"display_name": "GPT-4o",        "description": "OpenAI flagship multimodal model"},
    "gpt-4o-mini":             {"display_name": "GPT-4o Mini",   "description": "Fast, affordable GPT-4o"},
    "gpt-4-turbo":             {"display_name": "GPT-4 Turbo",   "description": "High-capability GPT-4"},
    "gpt-3.5-turbo":           {"display_name": "GPT-3.5 Turbo", "description": "Fast, cost-effective reasoning"},
    # Google
    "gemini-2.0-flash":        {"display_name": "Gemini 2.0 Flash", "description": "Next-gen multimodal Gemini"},
    "gemini-1.5-pro":          {"display_name": "Gemini 1.5 Pro",   "description": "Long-context multimodal reasoning"},
    "gemini-1.5-flash":        {"display_name": "Gemini 1.5 Flash", "description": "Fast Gemini for most tasks"},
}


@router.get("", response_model=APIResponse[ModelsResponse])
async def list_models():
    """Return available AI providers and models based on configured API keys."""
    dispatcher = get_dispatcher()
    available = dispatcher.available_providers()

    provider_model_map = {
        "groq":   settings.groq_supported_models,
        "openai": settings.openai_supported_models,
        "google": settings.google_supported_models,
    }

    providers = []
    for pname in available:
        meta = _PROVIDER_META.get(pname, {"display_name": pname.capitalize(), "description": ""})
        models = []
        for model_id in provider_model_map.get(pname, []):
            m_meta = _MODEL_META.get(model_id, {"display_name": model_id, "description": ""})
            models.append({
                "id": model_id,
                "display_name": m_meta["display_name"],
                "description": m_meta["description"],
                "provider": pname,
            })
        providers.append({
            "name": pname,
            "display_name": meta["display_name"],
            "description": meta["description"],
            "models": models,
        })

    # Resolve default provider/model
    try:
        default_provider, default_model = dispatcher.resolve_provider_and_model()
    except Exception:
        default_provider = settings.ai_provider
        default_model = settings.groq_default_model

    return APIResponse(
        data=ModelsResponse(
            default_provider=default_provider,
            default_model=default_model,
            providers=providers,
        )
    )
