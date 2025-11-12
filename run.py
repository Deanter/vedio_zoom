#!/usr/bin/env python3
"""
Точка входа для запуска сервера транскрибации видео.
"""

import os
from app.main import create_app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)

