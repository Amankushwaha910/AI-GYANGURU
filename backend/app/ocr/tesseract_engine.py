"""
Tesseract OCR engine implementation (fallback OCR engine).
"""
import asyncio

from app.core.config import settings
from app.core.exceptions import FileProcessingError
from app.ocr.base import BaseOCREngine


class TesseractOCREngine(BaseOCREngine):
    def get_engine_name(self) -> str:
        return "tesseract"

    async def extract_from_image(self, image_bytes: bytes) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_tesseract, image_bytes)

    def _run_tesseract(self, image_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image
            import io

            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
            img = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(img)

        except Exception as exc:
            raise FileProcessingError(f"Tesseract OCR extraction failed: {exc}") from exc
