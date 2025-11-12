from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .downloader import VideoMetadata
from .models import Platform


@dataclass
class NormalizedMetadata:
    title: str
    author: str
    description: Optional[str]
    duration: Optional[float]
    url: str


def normalize_metadata(platform: Platform, metadata: VideoMetadata) -> NormalizedMetadata:
    title = metadata.title or "Untitled video"
    author = metadata.uploader or "Unknown author"
    description = (metadata.description or "").strip() or None

    if platform in {Platform.TIKTOK, Platform.INSTAGRAM}:
        # Для TikTok и Instagram описание можно опускать
        description = description or None

    duration = metadata.duration
    url = metadata.webpage_url or ""

    return NormalizedMetadata(
        title=title.strip(),
        author=author.strip(),
        description=description,
        duration=duration,
        url=url,
    )

