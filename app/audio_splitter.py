from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List


class AudioSplitError(RuntimeError):
    """Ошибка при разделении аудиофайла."""


def split_audio_by_size(
    audio_path: Path,
    output_dir: Path,
    max_size_mb: float = 24.0,
    chunk_duration_seconds: int = 600,
) -> List[Path]:
    """
    Разделяет аудиофайл на части, если он превышает максимальный размер.

    Args:
        audio_path: Путь к исходному аудиофайлу
        output_dir: Директория для сохранения частей
        max_size_mb: Максимальный размер части в МБ (по умолчанию 24 МБ для запаса)
        chunk_duration_seconds: Длительность каждой части в секундах (по умолчанию 10 минут)

    Returns:
        Список путей к частям аудио. Если файл меньше лимита, возвращает [audio_path]
    """
    if not audio_path.exists():
        raise AudioSplitError(f"Audio file not found: {audio_path}")

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)

    # Если файл меньше лимита, возвращаем его как есть
    if file_size_mb <= max_size_mb:
        return [audio_path]

    print(f"[INFO] Audio file size ({file_size_mb:.2f} MB) exceeds limit ({max_size_mb} MB). Splitting...")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = str(output_dir / f"{audio_path.stem}_chunk_%03d.wav")

    # Разделяем файл на части по времени с помощью ffmpeg
    command = [
        "ffmpeg",
        "-y",  # Перезаписывать существующие файлы
        "-i",
        str(audio_path),
        "-f",
        "segment",  # Использовать сегментацию
        "-segment_time",
        str(chunk_duration_seconds),  # Длительность каждого сегмента
        "-c",
        "copy",  # Копировать без перекодирования (быстрее)
        "-reset_timestamps",
        "1",  # Сбросить временные метки для каждого сегмента
        "-loglevel",
        "error",
        output_pattern,
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise AudioSplitError(f"Failed to split audio: {exc.stderr}") from exc

    # Собираем список созданных файлов
    chunks = sorted(output_dir.glob(f"{audio_path.stem}_chunk_*.wav"))

    if not chunks:
        raise AudioSplitError("No chunks were created during splitting")

    print(f"[INFO] Audio split into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        chunk_size_mb = chunk.stat().st_size / (1024 * 1024)
        print(f"[INFO]   Chunk {i+1}: {chunk_size_mb:.2f} MB")

    return chunks
