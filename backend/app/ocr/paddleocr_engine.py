"""
PaddleOCR engine implementation (primary OCR engine).
"""
import asyncio
from functools import lru_cache

from app.core.exceptions import FileProcessingError
from app.ocr.base import BaseOCREngine


class PaddleOCREngine(BaseOCREngine):
    def __init__(self) -> None:
        self._ocr = None  # Lazy init — PaddleOCR takes time to load

    def _get_ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            except ImportError:
                raise FileProcessingError(
                    "PaddleOCR is not installed. Run: pip install paddleocr"
                )
        return self._ocr

    def get_engine_name(self) -> str:
        return "paddleocr"

    async def extract_from_image(self, image_bytes: bytes) -> str:
        """Run PaddleOCR in a thread pool to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_ocr, image_bytes)

    def _run_ocr(self, image_bytes: bytes) -> str:
        try:
            import numpy as np
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(img)

            ocr = self._get_ocr()
            result = ocr.ocr(img_array, cls=True)

            if not result or not result[0]:
                return ""

            lines = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]
                    lines.append(text)

            return "\n".join(lines)

        except Exception as exc:
            raise FileProcessingError(f"PaddleOCR extraction failed: {exc}") from exc
