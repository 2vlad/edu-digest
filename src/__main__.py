#!/usr/bin/env python3
"""
Запуск админ-панели как модуля: python -m src
"""

from .admin_panel import app, FLASK_PORT, create_templates
from .database import init_database, test_db

if __name__ == '__main__':
    # Инициализируем базу данных при первом запуске
    print("🔧 Инициализация базы данных...")
    try:
        init_database()
        if test_db():
            print("✅ База данных готова к работе")
        else:
            print("⚠️ База данных требует проверки")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
    
    # Создаем шаблоны если их нет
    create_templates()
    
    print("🌐 Flask админ-панель запущена!")
    print(f"📍 Адрес: http://localhost:{FLASK_PORT}")
    print("🔧 Доступные функции:")
    print("   - Управление каналами (добавление, редактирование, удаление)")
    print("   - Настройки системы")  
    print("   - Просмотр логов запусков")
    print("   - Запуск сбора новостей")
    print("   - API endpoints")
    print("   - Health check")
    
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)