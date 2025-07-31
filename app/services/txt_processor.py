from .processor import DocumentProcessor
from fastapi import UploadFile, HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor


class TXTProcessor(DocumentProcessor):
    """Обработчик TXT файлов"""

    def get_supported_types(self) -> list[str]:
        return ["text/plain", "text/markdown"]

    async def validate(self, file: UploadFile) -> None:
        """Валидация TXT файла"""
        await super().validate(file)

        if file.content_type not in self.get_supported_types():
            raise HTTPException(
                status_code=400,
                detail="Только TXT/Markdown файлы разрешены",
            )

    async def extract_text(self, file: UploadFile) -> str:
        """Извлечение текста из TXT файла"""
        await self.validate(file)

        # Читаем содержимое файла напрямую (без CPU-интенсивных операций)
        content = await file.read()

        # Декодируем в строку в отдельном потоке (на случай больших файлов)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            text = await loop.run_in_executor(
                executor, self._decode_content, content
            )

        return text.strip()

    def _decode_content(self, content: bytes) -> str:
        """Декодирование байтов в строку"""
        try:
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'windows-1251', 'cp866']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # Если ничего не подошло, используем utf-8 с игнорированием ошибок
            return content.decode('utf-8', errors='ignore')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка декодирования текста: {str(e)}"
            )
