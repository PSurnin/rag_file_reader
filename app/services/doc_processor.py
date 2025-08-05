from .processor import DocumentProcessor
from fastapi import UploadFile, HTTPException
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

# WORK IN PROGRESS


class DOCProcessor(DocumentProcessor):
    """Обработчик DOC/DOCX файлов"""

    def get_supported_types(self) -> list[str]:
        return ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    async def validate(self, file: UploadFile) -> None:
        """Валидация DOC/DOCX файла"""
        await super().validate(file)

        if file.content_type not in self.get_supported_types():
            raise HTTPException(
                status_code=400,
                detail="Только DOC/DOCX файлы разрешены",
            )

    async def extract_text(self, file: UploadFile) -> str:
        """Асинхронное извлечение текста из DOC/DOCX"""
        await self.validate(file)

        # Читаем содержимое файла
        content = await file.read()

        # CPU-интенсивную работу выполняем в thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            text = await loop.run_in_executor(
                executor, self._extract_text_sync, content
            )

        return text.strip() if text else ""

    def _extract_text_sync(self, content: bytes) -> str:
        """Синхронное извлечение текста (выполняется в отдельном потоке)"""
        try:
            # Импортируем только при необходимости
            from docx import Document
            import docx2txt

            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(content)
                tmp.flush()

                # Для DOCX файлов
                if tmp.name.endswith('.docx'):
                    doc = Document(tmp.name)
                    text = '\n'.join(
                        [paragraph.text for paragraph in doc.paragraphs]
                    )
                # Для DOC файлов (требует дополнительной библиотеки)
                else:
                    text = docx2txt.process(tmp.name)

                return text

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Не установлены необходимые библиотеки для обработки DOC/DOCX файлов"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка извлечения текста из документа: {str(e)}"
            )
