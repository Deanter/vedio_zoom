#!/bin/bash
# Тестовый запрос к сервису транскрибации

curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/shorts/5uG_zn02Ads"
  }' \
  | python3 -m json.tool

