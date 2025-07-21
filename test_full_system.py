#!/usr/bin/env python3
"""
Полный тест системы перед деплоем на Railway
"""

import asyncio
import sys
import os
sys.path.append('src')

def test_imports():
    """Проверяем, что все модули импортируются"""
    print("🧪 Тестируем импорты...")
    
    try:
        from src.admin_panel import app
        print("✅ admin_panel импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта admin_panel: {e}")
        return False
    
    try:
        from src.news_collector import NewsCollector
        print("✅ NewsCollector импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта NewsCollector: {e}")
        return False
    
    try:
        from src.database import init_database, ChannelsDB
        print("✅ Database модули импортированы")
    except Exception as e:
        print(f"❌ Ошибка импорта database: {e}")
        return False
    
    return True

def test_environment():
    """Проверяем переменные окружения"""
    print("\n🔑 Проверяем переменные окружения...")
    
    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Отсутствуют переменные: {', '.join(missing)}")
        return False
    else:
        print("✅ Все переменные окружения настроены")
        return True

def test_database():
    """Проверяем базу данных"""
    print("\n💾 Тестируем базу данных...")
    
    try:
        from src.database import init_database, test_db, ChannelsDB
        
        # Инициализируем БД
        init_database()
        print("✅ База данных инициализирована")
        
        # Тестируем подключение
        if test_db():
            print("✅ Подключение к БД работает")
        else:
            print("❌ Проблемы с подключением к БД")
            return False
        
        # Тестируем добавление канала
        try:
            ChannelsDB.add_channel("@test_channel", "Test Channel", 5)
            print("✅ Добавление каналов работает")
        except Exception as e:
            if "уже существует" in str(e):
                print("✅ Добавление каналов работает (канал уже существует)")
            else:
                print(f"❌ Ошибка добавления канала: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования БД: {e}")
        return False

async def test_news_collector():
    """Проверяем NewsCollector"""
    print("\n📰 Тестируем NewsCollector...")
    
    try:
        from src.news_collector import NewsCollector
        
        # Создаем коллектор
        collector = NewsCollector()
        print("✅ NewsCollector создан")
        
        # Инициализируем
        await collector.initialize()
        print("✅ NewsCollector инициализирован")
        
        # Тестируем форматирование
        test_messages = [{
            'id': 1,
            'text': 'Тестовая новость EdTech',
            'channel': '@test',
            'link': 'https://t.me/test/1',
            'summary': 'Тест форматирования дайджеста',
            'priority': 5
        }]
        
        digest = collector.format_digest(test_messages)
        print("✅ Форматирование дайджеста работает")
        print(f"   Длина: {len(digest)} символов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования NewsCollector: {e}")
        return False

def test_flask_app():
    """Проверяем Flask приложение"""
    print("\n🌐 Тестируем Flask приложение...")
    
    try:
        from src.admin_panel import app
        
        with app.test_client() as client:
            # Тестируем health check
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health check работает")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
            
            # Тестируем главную страницу
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Главная страница работает")
            else:
                print(f"❌ Главная страница failed: {response.status_code}")
                return False
            
            # Тестируем API статистики
            response = client.get('/api/stats')
            if response.status_code == 200:
                print("✅ API статистики работает")
            else:
                print(f"❌ API статистики failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования Flask: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🚀 Полное тестирование системы перед деплоем\n")
    
    tests = [
        ("Импорты", test_imports()),
        ("Переменные окружения", test_environment()),
        ("База данных", test_database()),
        ("NewsCollector", await test_news_collector()),
        ("Flask приложение", test_flask_app()),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   ✅ Пройдено: {passed}")
    print(f"   ❌ Провалено: {failed}")
    print(f"   📈 Процент успеха: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Готово к деплою на Railway!")
        return True
    else:
        print("\n⚠️ Есть проблемы, исправьте перед деплоем")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)