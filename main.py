#!/usr/bin/env python3
"""
Основной модуль запуска EdTech News Digest Bot
"""
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def run_collect():
    """Запуск сбора и публикации новостей"""
    from src.news_collector import NewsCollector
    
    collector = NewsCollector()
    result = await collector.run_full_cycle()
    
    if result["success"]:
        print("✅ Сбор новостей завершен успешно!")
        print(f"📊 Обработано: {result['channels_processed']} каналов, {result['messages_collected']} сообщений")
        print(f"📰 Опубликовано: {result['news_published']} новостей")
        return 0
    else:
        print(f"❌ Ошибка сбора новостей: {result.get('error', 'Unknown error')}")
        return 1

def run_admin():
    """Запуск Flask админ-панели"""
    try:
        from src.admin_panel import app
        from src.config import FLASK_PORT
        print(f"🌐 Запуск админ-панели на http://localhost:{FLASK_PORT}")
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
        return 0
    except ImportError as e:
        print(f"⚠️  Ошибка импорта админ-панели: {e}")
        print("🔧 Убедитесь что все зависимости установлены: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Ошибка запуска админ-панели: {e}")
        return 1

if __name__ == "__main__":
    print("EdTech News Digest Bot v0.1.0")
    print("="*40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "collect":
            print("🚀 Запуск сбора и публикации новостей...")
            exit_code = asyncio.run(run_collect())
            sys.exit(exit_code)
            
        elif command == "admin":
            print("🌐 Запуск админ-панели...")
            sys.exit(run_admin())
            
        elif command == "test":
            print("🧪 Запуск тестового режима...")
            # Запуск с симуляцией данных
            exit_code = asyncio.run(run_collect())
            sys.exit(exit_code)
            
        else:
            print(f"❌ Неизвестная команда: {command}")
            sys.exit(1)
    else:
        print("Доступные команды:")
        print("  python main.py collect  - Сбор и публикация новостей")
        print("  python main.py admin    - Запуск админ-панели")
        print("  python main.py test     - Тестовый режим")
        print()
        print("Примеры использования:")
        print("  python main.py collect  # Полный цикл сбора")
        print("  python main.py admin    # Веб-интерфейс на :5000")