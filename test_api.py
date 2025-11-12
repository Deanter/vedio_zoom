#!/usr/bin/env python3
"""
Простой скрипт для тестирования API транскрибации видео.
"""

import json
import sys
from pathlib import Path

import requests

# URL сервиса (по умолчанию localhost:8000)
API_URL = "http://localhost:8000/analyze"

# Примеры тестовых URL
TEST_URLS = {
    "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Короткое видео для быстрого теста
    "youtube_short": "https://www.youtube.com/shorts/example",  # Замените на реальный shorts
    "tiktok": "https://www.tiktok.com/@username/video/1234567890",  # Замените на реальный URL
    "instagram": "https://www.instagram.com/reel/ABC123/",  # Замените на реальный URL
}


def test_analyze(url: str):
    """Отправляет запрос на анализ видео."""
    print(f"\n🔍 Тестирую URL: {url}")
    print(f"📡 Отправляю запрос на {API_URL}...")

    try:
        response = requests.post(
            API_URL,
            json={"url": url},
            headers={"Content-Type": "application/json"},
            timeout=300,  # 5 минут на обработку
        )

        print(f"📊 Статус ответа: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ Успешный ответ:")
            print(f"   Платформа: {data.get('platform')}")
            print(f"   Название: {data.get('title')}")
            print(f"   Автор: {data.get('author')}")
            print(f"   Длительность: {data.get('duration')} сек")
            print(f"   Язык: {data.get('language', 'не определен')}")
            print(f"   Длина транскрипции: {len(data.get('transcript', ''))} символов")
            print(f"   Количество таймкодов: {len(data.get('timestamps', []))}")
            print(f"   Trace ID: {data.get('trace_id')}")

            # Показываем первые 3 таймкода
            timestamps = data.get("timestamps", [])
            if timestamps:
                print("\n   Первые таймкоды:")
                for ts in timestamps[:3]:
                    print(f"     {ts['time']}: {ts['text'][:50]}...")

            # Сохраняем полный ответ в файл
            output_file = Path("test_response.json")
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Полный ответ сохранен в {output_file}")

        else:
            print(f"\n❌ Ошибка: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Сообщение: {error_data.get('error', 'Unknown error')}")
                print(f"   Trace ID: {error_data.get('trace_id', 'N/A')}")
            except:
                print(f"   Текст ответа: {response.text[:200]}")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Не удалось подключиться к серверу на {API_URL}")
        print("   Убедитесь, что сервер запущен: python app/main.py")
    except requests.exceptions.Timeout:
        print("\n⏱️  Превышено время ожидания (5 минут)")
        print("   Видео может быть слишком длинным или есть проблемы с сетью")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")


def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        # Если передан URL как аргумент
        test_analyze(sys.argv[1])
    else:
        # Интерактивный режим
        print("=" * 60)
        print("Тестирование API транскрибации видео")
        print("=" * 60)
        print("\nВыберите тестовый URL:")
        print("1. YouTube (пример)")
        print("2. YouTube Shorts (нужно указать реальный URL)")
        print("3. TikTok (нужно указать реальный URL)")
        print("4. Instagram (нужно указать реальный URL)")
        print("5. Ввести свой URL")

        choice = input("\nВаш выбор (1-5): ").strip()

        if choice == "1":
            test_analyze(TEST_URLS["youtube"])
        elif choice == "2":
            url = input("Введите URL YouTube Shorts: ").strip()
            test_analyze(url if url else TEST_URLS["youtube_short"])
        elif choice == "3":
            url = input("Введите URL TikTok: ").strip()
            test_analyze(url if url else TEST_URLS["tiktok"])
        elif choice == "4":
            url = input("Введите URL Instagram: ").strip()
            test_analyze(url if url else TEST_URLS["instagram"])
        elif choice == "5":
            url = input("Введите URL: ").strip()
            if url:
                test_analyze(url)
            else:
                print("❌ URL не указан")
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    main()

