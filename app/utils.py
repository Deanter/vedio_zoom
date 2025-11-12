from __future__ import annotations

import math
import os
import uuid
from pathlib import Path
from typing import Iterable


def format_timestamp(seconds: float) -> str:
    """Конвертирует секунды в формат HH:MM:SS с округлением вниз."""
    seconds_int = max(0, int(math.floor(seconds)))
    hours, remainder = divmod(seconds_int, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def generate_trace_id() -> str:
    return uuid.uuid4().hex


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_paths(paths: Iterable[Path]) -> None:
    """Удаляет перечисленные файлы/директории, игнорируя ошибки."""
    for path in paths:
        try:
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                for root, _, files in os.walk(path, topdown=False):
                    for file_name in files:
                        Path(root, file_name).unlink(missing_ok=True)
                path.rmdir()
        except Exception:
            # Нам важна попытка очистки, но ошибки не должны останавливать конвейер
            continue

