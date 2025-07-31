from typing import Dict, Optional
from .processor import DocumentProcessor


class ProcessorRegistry:
    """Реестр обработчиков документов"""

    def __init__(self):
        self._processors: Dict[str, DocumentProcessor] = {}
        self._initialize_processors()

    def _initialize_processors(self):
        """Инициализация всех обработчиков"""
        from .pdf_processor import PDFProcessor
        from .txt_processor import TXTProcessor
        from .doc_processor import DOCProcessor

        processors = [
            PDFProcessor(),
            TXTProcessor(),
            DOCProcessor(),
        ]

        for processor in processors:
            for mime_type in processor.get_supported_types():
                self._processors[mime_type] = processor

    def get_processor(self, content_type: str) -> Optional[DocumentProcessor]:
        """Получение обработчика по MIME типу"""
        return self._processors.get(content_type)

    def get_supported_types(self) -> list[str]:
        """Получение всех поддерживаемых MIME типов"""
        return list(self._processors.keys())


# Глобальный реестр
registry = ProcessorRegistry()


# Удобные функции
def get_processor(content_type: str):
    return registry.get_processor(content_type)


def get_supported_types():
    return registry.get_supported_types()
