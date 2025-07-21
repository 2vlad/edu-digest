#!/usr/bin/env python3
"""
Запуск админ-панели как модуля: python -m src
"""

from .admin_panel import app, FLASK_PORT, create_templates

if __name__ == '__main__':
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