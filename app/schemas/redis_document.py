from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    done = "done"
    error = "error"


class DocumentDTO(BaseModel):
    document_id: str
    status: DocumentStatus
    text: str
    result: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    def dict_items(self):
        """Возвращает поля как итератор пар (ключ, значение)"""
        return self.dict().items()

    @classmethod
    def from_redis(cls, document_id: str, data: dict):
        """Собираем DTO из Redis словаря"""
        return cls(
            document_id=document_id,
            status=data.get("status", ""),
            text=data.get("text", ""),
            result=data.get("result") or None,
            created_at=datetime.fromisoformat(data.get("created_at")),
            updated_at=datetime.fromisoformat(data.get("updated_at")),
        )

    def to_redis(self) -> dict:
        """Готовим данные для Redis"""
        return {
            "status": self.status,
            "text": self.text,
            # избегаем None
            "result": self.result or "",
            # возвращаем строку для redis
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
