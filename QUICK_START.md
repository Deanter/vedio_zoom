# Быстрый старт

## Что работает сейчас

✅ **POST `/analyze`** - основной эндпоинт для анализа видео
- Принимает JSON: `{"url": "https://..."}`
- Возвращает унифицированный JSON с транскрипцией и метаданными
- Поддерживает: YouTube, TikTok, Instagram

## Установка и запуск

### 1. Установите зависимости

```bash
pip3 install -r requirements.txt
```

Или если используете виртуальное окружение:

```bash
python3 -m pip install -r requirements.txt
```

### 2. Настройте переменные окружения

Создайте файл `.env` (скопируйте из `.env.example`):

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваш OpenAI API ключ:

```
OPENAI_API_KEY=sk-your-key-here
WHISPER_MODEL=whisper-1
TEMP_DIR=/tmp/video_api
```

### 3. Убедитесь, что установлен ffmpeg

```bash
# Проверка
ffmpeg -version

# Если не установлен (macOS):
brew install ffmpeg

# Если не установлен (Linux):
sudo apt-get install ffmpeg
```

### 4. Запустите сервер

```bash
python3 run.py
```

Или альтернативный способ:

```bash
python3 -m app.main
```

Сервер запустится на `http://localhost:8000`

## Тестирование

### Вариант 1: Использовать тестовый скрипт

```bash
python3 test_api.py
```

Скрипт предложит выбрать платформу или ввести свой URL.

### Вариант 2: Использовать curl

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Вариант 3: Использовать Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
)

print(response.json())
```

## Формат ответа

```json
{
  "platform": "youtube",
  "url": "https://www.youtube.com/watch?v=...",
  "title": "Название видео",
  "author": "Автор",
  "description": "Описание (опционально)",
  "language": "ru",
  "duration": 123.5,
  "transcript": "Полный текст транскрипции...",
  "timestamps": [
    {"time": "00:00:00", "text": "Начало"},
    {"time": "00:00:12", "text": "Следующий сегмент"}
  ],
  "trace_id": "abc123..."
}
```

## Обработка ошибок

- **400** - Невалидный URL или неподдерживаемая платформа
- **500** - Ошибка при загрузке, транскрибации или обработке

## Примечания

- Первая обработка может занять время (скачивание + транскрибация)
- Временные файлы автоматически удаляются после обработки
- Для длинных видео процесс может занять несколько минут

