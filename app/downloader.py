from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from yt_dlp import YoutubeDL


@dataclass
class VideoMetadata:
    title: Optional[str]
    uploader: Optional[str]
    description: Optional[str]
    duration: Optional[float]
    webpage_url: Optional[str]


class DownloadError(RuntimeError):
    """Ошибка при загрузке видео."""


def download_video(url: str, temp_dir: Path, trace_id: str) -> Tuple[Path, VideoMetadata]:
    """
    Скачивает видео через yt-dlp и возвращает путь к файлу и метаданные.

    Файл сохраняется в temp_dir с именем, содержащим trace_id.
    """
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(temp_dir / f"{trace_id}.%(ext)s")

    ydl_opts = {
        # Используем worst/best - сначала пробуем худшее качество (обычно доступно),
        # если не получается - лучшее. Главное - получить файл для извлечения аудио
        "format": "worst/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,  # Временно включим вывод для отладки
        "no_warnings": False,
        "extract_flat": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "ignoreerrors": False,
        "no_check_certificate": False,
        # Настройки для надежного скачивания
        "retries": 3,  # Количество попыток при ошибках
        "fragment_retries": 3,  # Попытки для фрагментов (HLS)
        "file_access_retries": 3,  # Попытки доступа к файлу
        "retry_sleep": 2,  # Пауза между попытками (секунды)
        "socket_timeout": 30,  # Таймаут сокета
        "http_chunk_size": 10485760,  # Размер чанка для HTTP (10MB)
    }

    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Очищаем предыдущие попытки (удаляем неполные файлы)
            if attempt > 0:
                for ext in ["mp4", "webm", "mkv", "m4a", "mp3", "part"]:
                    partial_file = temp_dir / f"{trace_id}.{ext}"
                    if partial_file.exists():
                        try:
                            partial_file.unlink()
                        except Exception:
                            pass
                import time
                time.sleep(2)  # Пауза перед повторной попыткой
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = _resolve_output_path(info, ydl, temp_dir, trace_id)
                
                # Проверяем, что файл существует и не пустой
                if not file_path.exists():
                    raise DownloadError(f"Downloaded file not found: {file_path}")
                
                file_size = file_path.stat().st_size
                if file_size == 0:
                    raise DownloadError(f"Downloaded file is empty: {file_path}")
                
                if file_size < 1024:  # Меньше 1KB - подозрительно
                    raise DownloadError(f"Downloaded file is too small ({file_size} bytes): {file_path}")
                
                # Если дошли сюда - файл успешно скачан
                break
                
        except DownloadError:
            if attempt < max_retries:
                last_error = f"Download attempt {attempt + 1} failed, retrying..."
                continue
            raise
        except Exception as exc:  # pragma: no cover - yt-dlp errors are numerous
            if attempt < max_retries:
                last_error = f"Download attempt {attempt + 1} failed: {exc}, retrying..."
                continue
            raise DownloadError(f"Failed to download video after {max_retries + 1} attempts: {exc}") from exc
    else:
        # Если все попытки исчерпаны
        raise DownloadError(f"Failed to download video after {max_retries + 1} attempts. Last error: {last_error}")

    metadata = VideoMetadata(
        title=info.get("title"),
        uploader=info.get("uploader") or info.get("channel"),
        description=info.get("description"),
        duration=float(info["duration"]) if info.get("duration") is not None else None,
        webpage_url=info.get("webpage_url") or url,
    )

    return file_path, metadata


def _resolve_output_path(info: dict, ydl: YoutubeDL, temp_dir: Path, trace_id: str) -> Path:
    """
    Определяет фактический путь к скачанному файлу.

    yt-dlp может возвращать разные поля в зависимости от того, выполнялось ли
    объединение потоков и использовался ли ffmpeg.
    """
    candidates = []

    # Проверяем различные возможные пути
    if info.get("_filename"):
        candidates.append(Path(info["_filename"]))

    if info.get("requested_downloads"):
        for item in info["requested_downloads"]:
            if item.get("filepath"):
                candidates.append(Path(item["filepath"]))

    # Пробуем подготовить имя файла из метаданных
    try:
        prepared = ydl.prepare_filename(info)
        if prepared:
            candidates.append(Path(prepared))
    except Exception:
        pass

    # Ищем файлы в temp_dir с trace_id в имени
    for ext in ["mp4", "webm", "mkv", "m4a", "mp3"]:
        candidate = temp_dir / f"{trace_id}.{ext}"
        if candidate.exists():
            candidates.append(candidate)

    # Проверяем все кандидаты
    for path in candidates:
        if path.exists() and path.stat().st_size > 0:
            return path

    # Если ничего не найдено, ищем любой файл в temp_dir
    for file_path in temp_dir.glob("*"):
        if file_path.is_file() and file_path.stat().st_size > 0:
            return file_path

    raise DownloadError(f"Cannot determine downloaded file path. Checked: {[str(c) for c in candidates]}")

