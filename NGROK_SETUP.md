# Настройка ngrok для доступа к сервису

## Установка ngrok

### macOS (через Homebrew)
```bash
brew install ngrok/ngrok/ngrok
```

### Альтернативный способ (все платформы)
1. Скачайте ngrok с https://ngrok.com/download
2. Распакуйте и добавьте в PATH
3. Зарегистрируйтесь на https://ngrok.com (бесплатно)
4. Получите authtoken и выполните:
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

## Быстрый запуск

### Вариант 1: Автоматический скрипт (рекомендуется)

```bash
chmod +x start_with_ngrok.sh
./start_with_ngrok.sh
```

Скрипт автоматически:
- Запустит Flask сервер на порту 8000
- Запустит ngrok туннель
- Покажет публичный URL

### Вариант 2: Ручной запуск

**Терминал 1 - Flask сервер:**
```bash
python3 run.py
```

**Терминал 2 - ngrok:**
```bash
ngrok http 8000
```

## Использование в n8n

1. Получите публичный URL от ngrok (например: `https://abc123.ngrok-free.app`)
2. В n8n создайте HTTP Request узел:
   - **Method**: POST
   - **URL**: `https://abc123.ngrok-free.app/analyze`
   - **Headers**: 
     - `Content-Type: application/json`
   - **Body**:
     ```json
     {
       "url": "https://www.youtube.com/watch?v=..."
     }
     ```

## Пример запроса через curl

```bash
curl -X POST https://YOUR_NGROK_URL.ngrok-free.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## Важные замечания

1. **Бесплатный план ngrok:**
   - URL меняется при каждом перезапуске
   - Есть ограничения по трафику
   - Для продакшена лучше использовать платный план с фиксированным доменом

2. **Безопасность:**
   - ngrok URL публичный - любой может использовать ваш сервис
   - Рассмотрите добавление аутентификации для продакшена

3. **Остановка:**
   - Нажмите Ctrl+C в терминале со скриптом
   - Или остановите процессы вручную:
     ```bash
     pkill -f "python3 run.py"
     pkill ngrok
     ```

## Проверка статуса

- Веб-интерфейс ngrok: http://localhost:4040
- Проверка Flask сервера: http://localhost:8000

