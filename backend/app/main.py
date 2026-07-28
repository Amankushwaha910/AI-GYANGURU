"""
AI GyanGuru — FastAPI Application Entry Point
"""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("gyanguru")

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_general])

# ── App Instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI GyanGuru",
    description="AI-powered personal learning platform API",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# ── Middleware ────────────────────────────────────────────────────────────────

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS — only allow the registered frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Trusted hosts (production hardening)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["gyanguru.com", "*.gyanguru.com"],
    )


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Exception Handlers ────────────────────────────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.api_v1_prefix)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "AI GyanGuru API", "version": "1.0.0"}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI GyanGuru API",
        "docs": "/docs",
        "version": "1.0.0",
    }


# ── Startup / Shutdown Events ─────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("AI GyanGuru API starting up...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"AI Provider: {settings.ai_provider} | Model: {settings.groq_default_model}")
    logger.info(f"OCR Engine: {settings.ocr_engine}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AI GyanGuru API shutting down...")
