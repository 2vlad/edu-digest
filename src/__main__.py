#!/usr/bin/env python3
"""
Запуск админ-панели как модуля: python -m src
"""

from .admin_panel import app, FLASK_PORT, create_templates
from .database import init_database, test_db

if __name__ == '__main__':
    import logging
    # Настраиваем логирование для детального debug
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Flask application...")
    
    # Инициализируем базу данных при первом запуске
    logger.info("🔧 Initializing database...")
    try:
        init_database()
        if test_db():
            logger.info("✅ Database is ready")
            print("✅ База данных готова к работе")
        else:
            logger.warning("⚠️ Database needs verification")
            print("⚠️ База данных требует проверки")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        print(f"❌ Ошибка инициализации БД: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Создаем шаблоны если их нет
    logger.info("🎨 Creating templates...")
    create_templates()
    
    logger.info("🌐 Starting Flask server...")
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