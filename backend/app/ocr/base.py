"""
Abstract OCR engine interface.
Swapping OCR engines requires only a new implementation of this class.
"""
from abc import ABC, abstractmethod


class BaseOCREngine(ABC):
    @abstractmethod
    async def extract_from_image(self, image_bytes: bytes) -> str:
        """Extract text from image bytes. Returns plain text string."""
        ...

    @abstractmethod
    def get_engine_name(self) -> str:
        ...
