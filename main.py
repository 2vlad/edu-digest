#!/usr/bin/env python3
"""
Основной модуль запуска EdTech News Digest Bot
"""
import sys
import os
import asyncio
import logging
import traceback
from datetime import datetime

# Добавляем путь к src модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Настройка детального логирования для main.py
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_startup_info():
    """Логируем информацию о запуске системы"""
    logger.info("🚀 Starting EdTech News Digest Bot v1.0.0")
    logger.info("=" * 60)
    logger.info(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📍 Working directory: {os.getcwd()}")
    logger.info(f"🗂️ Script path: {os.path.abspath(__file__)}")
    logger.info(f"📋 Command line: {' '.join(sys.argv)}")
    logger.info(f"🌍 Environment variables count: {len(os.environ)}")
    logger.info("=" * 60)
    
    # Логируем ключевые переменные окружения (без значений)
    key_vars = ['RAILWAY_ENVIRONMENT', 'PORT', 'TELEGRAM_API_ID', 'DATABASE_URL', 'SUPABASE_URL']
    logger.info("🔍 Key environment variables status:")
    for var in key_vars:
        status = "✅ Set" if os.getenv(var) else "❌ Missing"
        logger.info(f"   {var}: {status}")

# Выполняем логирование при импорте
log_startup_info()

async def run_collect():
    """Запуск сбора и публикации новостей"""
    logger.info("📡 Starting news collection cycle...")
    
    try:
        logger.info("📦 Importing NewsCollector module...")
        from src.news_collector import NewsCollector
        
        logger.info("🔧 Initializing NewsCollector...")
        collector = NewsCollector()
        
        logger.info("🚀 Running full news collection cycle...")
        start_time = datetime.now()
        result = await collector.run_full_cycle()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"⏱️ Collection cycle completed in {duration:.2f} seconds")
        
        if result["success"]:
            logger.info("✅ News collection completed successfully!")
            logger.info(f"📊 Processed: {result['channels_processed']} channels, {result['messages_collected']} messages")
            logger.info(f"📰 Published: {result['news_published']} news items")
            
            print("✅ Сбор новостей завершен успешно!")
            print(f"📊 Обработано: {result['channels_processed']} каналов, {result['messages_collected']} сообщений")
            print(f"📰 Опубликовано: {result['news_published']} новостей")
            return 0
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ News collection failed: {error_msg}")
            
            if 'telegram' in error_msg.lower():
                logger.error("💡 Likely cause: Telegram API credentials missing or invalid")
                logger.error("🔧 Check TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables")
            elif 'database' in error_msg.lower():
                logger.error("💡 Likely cause: Database connection issues")
                logger.error("🔧 Check DATABASE_URL and Supabase configuration")
                
            print(f"❌ Ошибка сбора новостей: {error_msg}")
            return 1
            
    except ImportError as import_error:
        logger.error(f"❌ CRITICAL: Failed to import required modules: {import_error}")
        logger.error("🔧 Check that all dependencies are installed and src/ path is correct")
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        print(f"❌ Ошибка импорта модулей: {import_error}")
        return 1
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: Unexpected error during news collection: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        print(f"❌ Критическая ошибка: {e}")
        return 1

def run_admin():
    """Запуск Flask админ-панели"""
    logger.info("🌐 Starting Flask admin panel...")
    
    try:
        logger.info("📦 Importing admin panel module...")
        from src.admin_panel import app
        from src.config import FLASK_PORT
        
        logger.info(f"🚀 Starting Flask server on 0.0.0.0:{FLASK_PORT}")
        logger.info(f"📍 Admin panel URL: http://localhost:{FLASK_PORT}")
        
        print(f"🌐 Запуск админ-панели на http://localhost:{FLASK_PORT}")
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
        
        logger.info("✅ Flask admin panel started successfully")
        return 0
        
    except ImportError as import_error:
        logger.error(f"❌ CRITICAL: Failed to import admin panel modules: {import_error}")
        logger.error("🔧 Check that all dependencies are installed")
        logger.error("💡 Run: pip install -r requirements.txt")
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        
        print(f"⚠️  Ошибка импорта админ-панели: {import_error}")
        print("🔧 Убедитесь что все зависимости установлены: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to start admin panel: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        
        print(f"❌ Ошибка запуска админ-панели: {e}")
        return 1

if __name__ == "__main__":
    logger.info("🎯 Main script execution started")
    print("EdTech News Digest Bot v0.1.0")
    print("="*40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        logger.info(f"📋 Command received: {command}")
        
        if command == "collect":
            logger.info("🎯 Executing: news collection")
            print("🚀 Запуск сбора и публикации новостей...")
            exit_code = asyncio.run(run_collect())
            logger.info(f"🏁 News collection finished with exit code: {exit_code}")
            sys.exit(exit_code)
            
        elif command == "admin":
            logger.info("🎯 Executing: admin panel")
            print("🌐 Запуск админ-панели...")
            exit_code = run_admin()
            logger.info(f"🏁 Admin panel finished with exit code: {exit_code}")
            sys.exit(exit_code)
            
        elif command == "test":
            logger.warning("⚠️ Test mode requested - but SIMULATION IS DISABLED in production!")
            logger.warning("🚫 Test mode redirects to real data collection")
            print("🧪 Запуск тестового режима (перенаправлено на реальный сбор)...")
            # В production режиме всегда используем реальные данные
            exit_code = asyncio.run(run_collect())
            logger.info(f"🏁 Test mode finished with exit code: {exit_code}")
            sys.exit(exit_code)
            
        else:
            logger.error(f"❌ Unknown command received: {command}")
            logger.error("💡 Available commands: collect, admin, test")
            print(f"❌ Неизвестная команда: {command}")
            print("💡 Используйте: collect, admin, test")
            sys.exit(1)
    else:
        logger.info("ℹ️ No command specified, showing help")
        print("Доступные команды:")
        print("  python main.py collect  - Сбор и публикация новостей")
        print("  python main.py admin    - Запуск админ-панели")
        print("  python main.py test     - Тестовый режим (используется реальные данные)")
        print()
        logger.info("🏁 Help displayed, exiting")
        sys.exit(0)