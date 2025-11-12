#!/bin/bash
# Production server script with extended timeout for long-running transcriptions

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Start gunicorn with configuration for long-running requests
gunicorn \
    --workers 2 \
    --timeout 600 \
    --graceful-timeout 600 \
    --keep-alive 5 \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "app.main:app"
