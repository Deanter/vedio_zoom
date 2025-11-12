#!/bin/bash
# Скрипт для запуска сервера с ngrok

echo "🚀 Запуск сервера транскрибации с ngrok..."

# Проверяем, установлен ли ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok не установлен!"
    echo "Установите ngrok:"
    echo "  macOS: brew install ngrok/ngrok/ngrok"
    echo "  Или скачайте с https://ngrok.com/download"
    exit 1
fi

# Проверяем, запущен ли уже ngrok
if pgrep -x "ngrok" > /dev/null; then
    echo "⚠️  ngrok уже запущен. Останавливаю существующий процесс..."
    pkill ngrok
    sleep 2
fi

# Запускаем production сервер (gunicorn) в фоне для поддержки длинных транскрипций
echo "📡 Запуск production сервера на порту 8000..."
# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "✅ OPENAI_API_KEY загружен (длина: ${#OPENAI_API_KEY} символов)"
    else
        echo "⚠️  OPENAI_API_KEY не найден в .env!"
    fi
fi
gunicorn --workers 2 --timeout 600 --graceful-timeout 600 --bind 0.0.0.0:8000 --daemon --pid gunicorn.pid "app.main:app"
# Ждем создания PID файла
sleep 2
FLASK_PID=$(cat gunicorn.pid 2>/dev/null || echo "")

# Ждем немного, чтобы сервер запустился
sleep 3

# Проверяем, что сервер запустился
if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "❌ Сервер не запустился. Проверьте ошибки выше."
    kill $FLASK_PID 2>/dev/null
    exit 1
fi

echo "✅ Flask сервер запущен (PID: $FLASK_PID)"

# Запускаем ngrok
echo "🌐 Запуск ngrok туннеля..."
ngrok http 8000 > /dev/null &
NGROK_PID=$!

# Ждем запуска ngrok
sleep 3

# Получаем публичный URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Не удалось получить ngrok URL"
    echo "Проверьте, что ngrok запущен: http://localhost:4040"
    kill $FLASK_PID $NGROK_PID 2>/dev/null
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Сервис доступен по адресу:"
echo "   $NGROK_URL"
echo ""
echo "📋 Используйте этот URL в n8n:"
echo "   $NGROK_URL/analyze"
echo ""
echo "🔍 Веб-интерфейс ngrok: http://localhost:4040"
echo ""
echo "⏹️  Для остановки нажмите Ctrl+C"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Функция для очистки при выходе
cleanup() {
    echo ""
    echo "🛑 Остановка сервисов..."
    kill $NGROK_PID 2>/dev/null
    if [ -f gunicorn.pid ]; then
        kill $(cat gunicorn.pid) 2>/dev/null
        rm -f gunicorn.pid
    fi
    pkill -f gunicorn 2>/dev/null
    echo "✅ Остановлено"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Ждем завершения
wait

