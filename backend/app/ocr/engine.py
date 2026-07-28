"""
OCR engine factory — returns the configured engine instance.
"""
from functools import lru_cache

from app.core.config import settings
from app.ocr.base import BaseOCREngine


@lru_cache(maxsize=1)
def get_ocr_engine() -> BaseOCREngine:
    """Return the configured OCR engine singleton."""
    if settings.ocr_engine == "paddleocr":
        from app.ocr.paddleocr_engine import PaddleOCREngine
        return PaddleOCREngine()
    elif settings.ocr_engine == "tesseract":
        from app.ocr.tesseract_engine import TesseractOCREngine
        return TesseractOCREngine()
    else:
        raise ValueError(f"Unknown OCR engine: {settings.ocr_engine}")
