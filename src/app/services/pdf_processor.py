from src.app.services.processor import DocumentProcessor
from fastapi import UploadFile, HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
from io import BytesIO


class PDFProcessor(DocumentProcessor):
    """Асинхронный обработчик PDF файлов"""

    def get_supported_types(self) -> list[str]:
        return ["application/pdf"]

    async def validate(self, file: UploadFile) -> None:
        """Валидация PDF файла"""
        await super().validate(file)

        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Только PDF файлы разрешены",
            )

    async def extract_text(self, file: UploadFile) -> str:
        """Асинхронное извлечение текста из PDF"""
        await self.validate(file)

        # Асинхронно читаем содержимое файла
        content = await file.read()

        # CPU-работа
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            text = await loop.run_in_executor(
                executor, self._extract_text_sync, content
            )

        return text.strip() if text else ""

    def _extract_text_sync(self, content: bytes) -> str:
        """Синхронное извлечение текста (выполняется в отдельном потоке)"""
        try:
            reader = PdfReader(BytesIO(content))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка извлечения текста из PDF: {str(e)}"
            )
