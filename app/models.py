from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Platform(str, Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"


class AnalyzeRequest(BaseModel):
    url: HttpUrl = Field(..., description="HTTPS ссылка на видео в поддерживаемых платформах")


class TimestampEntry(BaseModel):
    time: str = Field(..., description="Время начала сегмента в формате HH:MM:SS")
    text: str = Field(..., description="Текст сегмента без форматирования")


class AnalyzeResponse(BaseModel):
    platform: Platform
    url: str  # Используем str вместо HttpUrl для сериализации в JSON
    title: str
    author: str
    description: Optional[str] = None
    language: Optional[str] = None
    duration: Optional[float] = Field(None, description="Длительность видео в секундах")
    transcript: str
    timestamps: List[TimestampEntry]
    trace_id: str

