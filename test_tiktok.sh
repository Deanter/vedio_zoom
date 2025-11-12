#!/bin/bash
# Тестовый запрос к сервису транскрибации для TikTok

curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://vm.tiktok.com/ZMA7r5y8B/"
  }' \
  | python3 -m json.tool

