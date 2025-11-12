# Video Transcription Service

Сервис для транскрибации видео по ссылке с YouTube, TikTok и Instagram. На вход принимает HTTPS ссылку, на выходе возвращает унифицированный JSON с метаданными, текстом и таймкодами.

## Возможности

- Автоматическое определение платформы по URL.
- Загрузка видео через `yt-dlp`.
- Извлечение аудио через `ffmpeg` в формат WAV 16 kHz mono.
- Транскрибация аудио через Whisper API (`openai`).
- Формирование таймкодов для каждого сегмента.
- Очистка временных файлов после обработки.

## Требования

- Python 3.10+
- Установленный `ffmpeg` (должен быть доступен в `PATH`)
- Действующий ключ OpenAI (`OPENAI_API_KEY`)


## Запуск

Рекомендуемый способ:

```bash
python3 run.py
```

Альтернативные способы:

```bash
# Через Flask CLI
export FLASK_APP=app.main:app
flask run --host=0.0.0.0 --port=8000

# Через модуль Python
python3 -m app.main
```

## API

### `POST /analyze`

Тело запроса:

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

Пример ответа:

```json
{
  "platform": "youtube",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Sample Title",
  "author": "Sample Uploader",
  "description": "Sample description text",
  "language": "en",
  "duration": 212.3,
  "transcript": "Full plain text transcript...",
  "timestamps": [
    { "time": "00:00:00", "text": "Intro" },
    { "time": "00:00:12", "text": "First topic" }
  ],
  "trace_id": "b7c7a7b0a3c54f5e8f3a9b11e1e3c2c8"
}
```

Описание:

- `platform` — определённая платформа (`youtube`, `tiktok`, `instagram`).
- `trace_id` — уникальный идентификатор запроса для трассировки.
- Поля `description` и `language` могут отсутствовать, если данных нет.

## Комментарии

- Для TikTok и Instagram описание в ответ не включается, если оно пустое.
- Все временные файлы (видео и аудио) удаляются после завершения обработки.
- Для обработки длинных роликов требуется достаточно дискового пространства во временной директории.

