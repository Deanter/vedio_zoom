from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from openai import OpenAI


@dataclass
class TranscriptionSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    language: Optional[str]
    segments: List[TranscriptionSegment]


class TranscriptionError(RuntimeError):
    """Ошибка при обращении к Whisper API."""


def transcribe_audio(audio_path: Path, model: str, client: Optional[OpenAI] = None) -> TranscriptionResult:
    if not audio_path.exists():
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    client = client or OpenAI()

    try:
        with audio_path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
            )
    except Exception as exc:  # pragma: no cover - сетевые ошибки трудно тестировать
        raise TranscriptionError(f"Whisper API request failed: {exc}") from exc

    text = getattr(response, "text", "") or ""
    language = getattr(response, "language", None)
    segments_data = getattr(response, "segments", []) or []

    segments: List[TranscriptionSegment] = []
    for segment in segments_data:
        start = float(getattr(segment, "start", 0.0) or 0.0)
        end = float(getattr(segment, "end", start) or start)
        seg_text = getattr(segment, "text", "") or ""

        if not seg_text.strip():
            continue

        segments.append(TranscriptionSegment(start=start, end=end, text=seg_text.strip()))

    return TranscriptionResult(text=text.strip(), language=language, segments=segments)

