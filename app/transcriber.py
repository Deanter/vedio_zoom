from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from .audio_splitter import AudioSplitError, split_audio_by_size


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


# Whisper API лимит: 25 МБ, используем 24 МБ для запаса
WHISPER_MAX_FILE_SIZE_MB = 24.0


def transcribe_audio(audio_path: Path, model: str, client: Optional[OpenAI] = None) -> TranscriptionResult:
    if not audio_path.exists():
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    client = client or OpenAI()

    # Проверяем размер файла и разделяем при необходимости
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    chunks_dir = audio_path.parent / f"{audio_path.stem}_chunks"

    try:
        if file_size_mb > WHISPER_MAX_FILE_SIZE_MB:
            print(f"[INFO] Audio file too large ({file_size_mb:.2f} MB), splitting into chunks...")
            audio_chunks = split_audio_by_size(audio_path, chunks_dir, WHISPER_MAX_FILE_SIZE_MB)
        else:
            audio_chunks = [audio_path]

        # Транскрибируем каждую часть
        all_segments: List[TranscriptionSegment] = []
        full_text_parts: List[str] = []
        detected_language: Optional[str] = None
        cumulative_duration = 0.0

        for chunk_idx, chunk_path in enumerate(audio_chunks):
            chunk_size_mb = chunk_path.stat().st_size / (1024 * 1024)
            print(f"[INFO] Transcribing chunk {chunk_idx + 1}/{len(audio_chunks)}: {chunk_path.name} ({chunk_size_mb:.2f} MB)")
            print(f"[INFO] Sending chunk to Whisper API... This may take 1-3 minutes.")

            chunk_result = _transcribe_single_file(chunk_path, model, client)

            print(f"[INFO] ✅ Chunk {chunk_idx + 1}/{len(audio_chunks)} transcribed: {len(chunk_result.segments)} segments, {len(chunk_result.text)} chars")

            # Сохраняем язык из первого чанка
            if chunk_idx == 0:
                detected_language = chunk_result.language

            # Добавляем текст
            if chunk_result.text:
                full_text_parts.append(chunk_result.text)

            # Добавляем сегменты с корректировкой временных меток
            for segment in chunk_result.segments:
                adjusted_segment = TranscriptionSegment(
                    start=segment.start + cumulative_duration,
                    end=segment.end + cumulative_duration,
                    text=segment.text,
                )
                all_segments.append(adjusted_segment)

            # Обновляем накопленную длительность для следующего чанка
            if chunk_result.segments:
                cumulative_duration = all_segments[-1].end

        # Объединяем результаты
        full_text = " ".join(full_text_parts)
        print(f"[INFO] ✅ All chunks processed. Total: {len(all_segments)} segments, {len(full_text)} chars")
        return TranscriptionResult(text=full_text.strip(), language=detected_language, segments=all_segments)

    except AudioSplitError as exc:
        raise TranscriptionError(f"Failed to split audio file: {exc}") from exc
    finally:
        # Очищаем временные файлы чанков
        if chunks_dir.exists():
            import shutil
            try:
                shutil.rmtree(chunks_dir)
            except Exception:
                pass  # Игнорируем ошибки очистки


def _transcribe_single_file(audio_path: Path, model: str, client: OpenAI) -> TranscriptionResult:
    """Транскрибирует один аудиофайл через Whisper API."""
    try:
        with audio_path.open("rb") as audio_file:
            print(f"[DEBUG] Sending request to Whisper API...")
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
            )
            print(f"[DEBUG] Received response from Whisper API")
    except Exception as exc:
        print(f"[ERROR] Whisper API error: {type(exc).__name__}: {exc}")
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

