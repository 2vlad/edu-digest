#!/usr/bin/env python3
"""
Скрипт для запуска админ-панели с правильной загрузкой окружения
"""
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

# Импортируем и запускаем
if __name__ == '__main__':
    from src.admin_panel import app
    port = int(os.getenv('PORT', 3000))
    print(f"🚀 Starting admin panel on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)