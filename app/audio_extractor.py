from __future__ import annotations

import subprocess
from pathlib import Path


class AudioExtractionError(RuntimeError):
    """Ошибка при извлечении аудио."""


def extract_audio(video_path: Path, temp_dir: Path, trace_id: str) -> Path:
    """
    Конвертирует видеофайл в WAV (моно, 16kHz) с помощью ffmpeg.

    Возвращает путь к созданному аудиофайлу.
    """
    if not video_path.exists():
        raise AudioExtractionError(f"Video file not found: {video_path}")

    temp_dir.mkdir(parents=True, exist_ok=True)
    audio_path = temp_dir / f"{trace_id}.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-loglevel",
        "error",
        str(audio_path),
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise AudioExtractionError(f"Failed to extract audio: {exc}") from exc

    if not audio_path.exists():
        raise AudioExtractionError("Audio extraction finished without creating a file.")

    return audio_path

