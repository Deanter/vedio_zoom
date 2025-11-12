from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from .audio_extractor import AudioExtractionError, extract_audio
from .downloader import DownloadError, download_video
from .metadata_processor import normalize_metadata
from .models import AnalyzeRequest, AnalyzeResponse, Platform, TimestampEntry
from .platform_detector import InvalidUrlError, detect_platform
from .transcriber import TranscriptionError, TranscriptionResult, transcribe_audio
from .utils import cleanup_paths, ensure_directory, format_timestamp, generate_trace_id

load_dotenv()

app = Flask(__name__)

TEMP_ROOT = Path(os.getenv("TEMP_DIR", "/tmp/video_api"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

# Проверка наличия API ключа
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables!")
else:
    print(f"✅ OPENAI_API_KEY loaded (length: {len(OPENAI_API_KEY)} chars)")


@app.post("/analyze")
def analyze():
    trace_id = generate_trace_id()

    payload = request.get_json(force=True, silent=False)
    request_data = AnalyzeRequest.model_validate(payload)
    url_str = str(request_data.url)

    try:
        platform = detect_platform(url_str)
    except InvalidUrlError as exc:
        return _json_error(str(exc), trace_id, status=400)

    work_dir = ensure_directory(TEMP_ROOT / trace_id)
    cleanup_targets: List[Path] = []

    try:
        # Этап 1: Скачивание видео
        try:
            print(f"[{trace_id}] Этап 1: Скачивание видео через yt-dlp...")
            video_path, raw_metadata = download_video(url_str, work_dir, trace_id)
            cleanup_targets.append(video_path)
            print(f"[{trace_id}] ✅ Видео скачано: {video_path} ({video_path.stat().st_size / 1024 / 1024:.2f} MB)")
        except DownloadError as exc:
            return _json_error(f"Ошибка скачивания видео (yt-dlp): {exc}", trace_id, status=500)
        except Exception as exc:
            return _json_error(f"Неожиданная ошибка при скачивании видео: {exc}", trace_id, status=500)

        # Этап 2: Извлечение аудио
        try:
            print(f"[{trace_id}] Этап 2: Извлечение аудио через ffmpeg...")
            audio_path = extract_audio(video_path, work_dir, trace_id)
            cleanup_targets.append(audio_path)
            print(f"[{trace_id}] ✅ Аудио извлечено: {audio_path} ({audio_path.stat().st_size / 1024 / 1024:.2f} MB)")
        except AudioExtractionError as exc:
            return _json_error(f"Ошибка извлечения аудио (ffmpeg): {exc}", trace_id, status=500)
        except Exception as exc:
            return _json_error(f"Неожиданная ошибка при извлечении аудио: {exc}", trace_id, status=500)

        # Этап 3: Обработка метаданных
        try:
            print(f"[{trace_id}] Этап 3: Обработка метаданных...")
            normalized_metadata = normalize_metadata(platform, raw_metadata)
            print(f"[{trace_id}] ✅ Метаданные обработаны")
        except Exception as exc:
            return _json_error(f"Ошибка обработки метаданных: {exc}", trace_id, status=500)

        # Этап 4: Транскрибация через Whisper API
        try:
            print(f"[{trace_id}] Этап 4: Транскрибация через Whisper API...")
            transcription = transcribe_audio(audio_path, WHISPER_MODEL)
            print(f"[{trace_id}] ✅ Транскрибация завершена: {len(transcription.segments)} сегментов, язык: {transcription.language}")
        except TranscriptionError as exc:
            print(f"[{trace_id}] ❌ TranscriptionError: {exc}")
            traceback.print_exc()
            return _json_error(f"Ошибка транскрибации (Whisper API): {exc}", trace_id, status=500)
        except Exception as exc:
            print(f"[{trace_id}] ❌ Unexpected error during transcription: {exc}")
            traceback.print_exc()
            return _json_error(f"Неожиданная ошибка при транскрибации: {exc}", trace_id, status=500)

        # Этап 5: Формирование ответа
        try:
            print(f"[{trace_id}] Этап 5: Формирование ответа...")
            full_text = transcription.text or " ".join(seg.text.strip() for seg in transcription.segments)
            timestamps = _build_timestamps(transcription)

            response_model = AnalyzeResponse(
                platform=platform,
                url=normalized_metadata.url or url_str,
                title=normalized_metadata.title,
                author=normalized_metadata.author,
                description=normalized_metadata.description,
                language=transcription.language,
                duration=normalized_metadata.duration,
                transcript=full_text.strip(),
                timestamps=timestamps,
                trace_id=trace_id,
            )

            print(f"[{trace_id}] ✅ Ответ сформирован успешно")
            return jsonify(response_model.model_dump(exclude_none=True))
        except Exception as exc:
            print(f"[{trace_id}] ❌ Error forming response: {exc}")
            traceback.print_exc()
            return _json_error(f"Ошибка формирования ответа: {exc}", trace_id, status=500)
    finally:
        # Выполняем очистку после обработки
        cleanup_targets.append(work_dir)
        cleanup_paths(cleanup_targets)


def _build_timestamps(transcription: TranscriptionResult) -> List[TimestampEntry]:
    entries: List[TimestampEntry] = []
    for segment in transcription.segments:
        text = segment.text.strip()
        if not text:
            continue
        entries.append(
            TimestampEntry(
                time=format_timestamp(segment.start),
                text=text,
            )
        )
    return entries


def _json_error(message: str, trace_id: str, status: int):
    payload = {"error": message, "trace_id": trace_id}
    return jsonify(payload), status


def create_app() -> Flask:
    """Фабрика приложения для использования во внешних сервисах/тестах."""
    return app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

