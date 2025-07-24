#!/usr/bin/env python3
"""
Скрипт проверки настройки Supabase для EdTech News Digest Bot
"""
import os
import sys

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def check_environment():
    """Проверка переменных окружения"""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = {
        'SUPABASE_URL': 'URL проекта Supabase',
        'SUPABASE_ANON_KEY': 'Anon/Public API Key из Supabase',
        'DATABASE_URL': 'PostgreSQL connection string'
    }
    
    optional_vars = {
        'TELEGRAM_API_ID': 'Telegram API ID',
        'TELEGRAM_API_HASH': 'Telegram API Hash',
        'TELEGRAM_BOT_TOKEN': 'Telegram Bot Token',
        'ANTHROPIC_API_KEY': 'Claude AI API Key'
    }
    
    missing_required = []
    missing_optional = []
    
    for var, desc in required_vars.items():
        if os.getenv(var):
            print(f"  ✅ {var}: {'*' * 20}... ({desc})")
        else:
            print(f"  ❌ {var}: НЕ НАСТРОЕН ({desc})")
            missing_required.append(var)
    
    for var, desc in optional_vars.items():
        if os.getenv(var):
            print(f"  ✅ {var}: {'*' * 20}... ({desc})")
        else:
            print(f"  ⚠️ {var}: НЕ НАСТРОЕН ({desc})")
            missing_optional.append(var)
    
    return missing_required, missing_optional

def test_supabase_connection():
    """Тестирование подключения к Supabase"""
    print("\n🔗 Тестирование подключения к Supabase...")
    
    try:
        from src.database import test_db, supabase_db
        
        # Попытка инициализации
        if supabase_db.initialize():
            print("  ✅ Подключение к Supabase установлено")
            
            # Тест базы данных
            if test_db():
                print("  ✅ Тест базы данных пройден")
                return True
            else:
                print("  ❌ Тест базы данных провалился")
                return False
        else:
            print("  ❌ Не удалось подключиться к Supabase")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка подключения: {e}")
        return False

def test_database_operations():
    """Тестирование операций с базой данных"""
    print("\n📊 Тестирование операций с базой данных...")
    
    try:
        from src.database import ChannelsDB, SettingsDB
        
        # Тест получения настроек
        test_setting = SettingsDB.get_setting('max_news_count', '10')
        print(f"  ✅ Настройка max_news_count: {test_setting}")
        
        # Тест получения каналов
        channels = ChannelsDB.get_active_channels()
        print(f"  ✅ Активных каналов: {len(channels)}")
        
        if channels:
            for i, channel in enumerate(channels[:3], 1):
                print(f"    {i}. {channel['username']} (приоритет: {channel['priority']})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка операций с БД: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Проверка настройки EdTech News Digest Bot (Supabase)")
    print("=" * 60)
    
    # Проверка переменных окружения
    missing_required, missing_optional = check_environment()
    
    if missing_required:
        print(f"\n❌ КРИТИЧЕСКИЕ ОШИБКИ: Отсутствуют обязательные переменные:")
        for var in missing_required:
            print(f"   - {var}")
        print("\n💡 Добавьте эти переменные в .env файл или environment")
        return False
    
    if missing_optional:
        print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЯ: Отсутствуют опциональные переменные:")
        for var in missing_optional:
            print(f"   - {var}")
        print("💡 Некоторые функции могут не работать без этих переменных")
    
    # Тест подключения к Supabase
    if not test_supabase_connection():
        print("\n❌ Не удалось подключиться к Supabase")
        print("💡 Проверьте правильность SUPABASE_URL, SUPABASE_ANON_KEY и DATABASE_URL")
        return False
    
    # Тест операций с базой данных
    if not test_database_operations():
        print("\n❌ Ошибка операций с базой данных")
        print("💡 Возможно, база данных не инициализирована. Запустите: python main.py init")
        return False
    
    print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("🎉 Система готова к работе!")
    print("\n📋 Следующие шаги:")
    print("  1. Добавьте каналы через админ-панель: python main.py admin")
    print("  2. Запустите сбор новостей: python main.py collect")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 