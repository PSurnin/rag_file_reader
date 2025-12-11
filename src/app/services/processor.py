from abc import ABC, abstractmethod
from fastapi import UploadFile, HTTPException


class DocumentProcessor(ABC):
    """Базовый класс для обработки документов"""

    def __init__(self, max_size: int = 50 * 1024 * 1024):
        self.max_size = max_size

    async def validate(self, file: UploadFile) -> None:
        """Базовая валидация файла"""
        if file.size > self.max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой (max {self.max_size//1024//1024}MB)",
            )

    @abstractmethod     # реализация обязательна
    async def extract_text(self, file: UploadFile) -> str:
        """Извлечение текста из файла"""
        pass

    @abstractmethod
    def get_supported_types(self) -> list[str]:
        """Поддерживаемые MIME типы"""
        pass
