#!/usr/bin/env python3
"""
Запуск админ-панели как модуля: python -m src
"""

from .admin_panel import app, FLASK_PORT
from .database import init_database, test_db, get_database_info

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
    
    # Показываем информацию о базе данных
    db_info = get_database_info()
    logger.info(f"🗄️ Database: {db_info}")
    print(f"🗄️ Database: {db_info['type']}")
    
    # Инициализируем базу данных при первом запуске
    logger.info("🔧 Initializing database...")
    try:
        init_database()
        if test_db():
            logger.info("✅ Database is ready")
            print("✅ База данных готова к работе")
            
            # Автоматически настраиваем каналы если их нет
            logger.info("📺 Checking EdTech channels...")
            try:
                from .database import ChannelsDB
                active_channels = ChannelsDB.get_active_channels()
                
                if len(active_channels) == 0:
                    logger.info("⚙️ No channels found - setting up EdTech channels...")
                    print("⚙️ Настраиваем каналы EdTech...")
                    
                    # Импортируем setup функцию
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                    
                    try:
                        from setup_channels import EDTECH_CHANNELS
                        
                        added_count = 0
                        for channel in EDTECH_CHANNELS:
                            try:
                                ChannelsDB.add_channel(
                                    username=channel["username"],
                                    display_name=channel["display_name"],
                                    priority=channel["priority"]
                                )
                                added_count += 1
                                logger.info(f"✅ Added channel: {channel['display_name']}")
                            except Exception:
                                # Игнорируем ошибки дублирования
                                pass
                        
                        logger.info(f"✅ Auto-setup completed: {added_count} channels added")
                        print(f"✅ Автоматически добавлено каналов: {added_count}")
                        
                    except Exception as setup_error:
                        logger.warning(f"⚠️ Channel auto-setup failed: {setup_error}")
                        print("⚠️ Автонастройка каналов не удалась - добавьте вручную через админ-панель")
                else:
                    logger.info(f"✅ Found {len(active_channels)} existing channels")
                    print(f"✅ Найдено каналов: {len(active_channels)}")
                    
            except Exception as channels_error:
                logger.warning(f"⚠️ Channel check failed: {channels_error}")
                print("⚠️ Не удалось проверить каналы")
            
        else:
            logger.warning("⚠️ Database needs verification")
            print("⚠️ База данных требует проверки")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        print(f"❌ Ошибка инициализации БД: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Шаблоны должны быть в папке templates
    logger.info("🎨 Templates should be in templates/ directory")
    
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