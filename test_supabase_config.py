#!/usr/bin/env python3
"""
Проверка настроек Supabase
Запуск: python test_supabase_config.py
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_supabase_config():
    """Проверяем все необходимые настройки Supabase"""
    print("🔍 Проверка конфигурации Supabase...")
    print()
    
    # Проверяем переменные
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    errors = []
    warnings = []
    
    # SUPABASE_URL
    if supabase_url:
        if supabase_url.startswith('https://') and '.supabase.co' in supabase_url:
            print(f"✅ SUPABASE_URL: {supabase_url}")
        else:
            print(f"⚠️  SUPABASE_URL: {supabase_url}")
            warnings.append("URL должен быть вида https://your-project.supabase.co")
    else:
        print("❌ SUPABASE_URL: не найден")
        errors.append("Добавьте SUPABASE_URL в переменные окружения")
    
    # SUPABASE_ANON_KEY
    if supabase_key:
        if supabase_key.startswith('eyJ') and len(supabase_key) > 100:
            print(f"✅ SUPABASE_ANON_KEY: {supabase_key[:20]}...{supabase_key[-10:]}")
        else:
            print(f"⚠️  SUPABASE_ANON_KEY: {supabase_key[:20]}... (возможно неправильный формат)")
            warnings.append("API ключ должен быть JWT токеном, начинающимся с 'eyJ'")
    else:
        print("❌ SUPABASE_ANON_KEY: не найден")
        errors.append("Добавьте SUPABASE_ANON_KEY в переменные окружения")
    
    # DATABASE_URL
    if database_url:
        if database_url.startswith('postgresql://') and 'supabase.co' in database_url:
            # Скрываем пароль в логах
            safe_url = database_url.replace(database_url.split('@')[0].split(':')[-1], '***')
            print(f"✅ DATABASE_URL: {safe_url}")
        else:
            print(f"⚠️  DATABASE_URL: {database_url[:30]}...")
            warnings.append("URL должен быть вида postgresql://postgres:password@db.your-project.supabase.co:5432/postgres")
    else:
        print("❌ DATABASE_URL: не найден")
        errors.append("Добавьте DATABASE_URL в переменные окружения")
    
    print()
    
    # Проверим подключение если все настроено
    if not errors:
        print("🧪 Тестируем подключение к Supabase...")
        try:
            from src.supabase_db import init_supabase_database, test_supabase_db
            
            # Инициализируем БД
            init_supabase_database()
            print("✅ Инициализация базы данных прошла успешно")
            
            # Тестируем подключение
            if test_supabase_db():
                print("✅ Подключение к Supabase работает!")
            else:
                print("❌ Подключение не работает")
                errors.append("Не удалось подключиться к базе данных")
                
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            errors.append(f"Ошибка подключения: {str(e)}")
    
    # Результаты
    print()
    print("=" * 50)
    if errors:
        print("❌ НАЙДЕНЫ ОШИБКИ:")
        for error in errors:
            print(f"   • {error}")
        print()
        print("📖 Смотрите инструкцию в SUPABASE_SETUP.md")
        return False
    elif warnings:
        print("⚠️  НАЙДЕНЫ ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
        print("🎯 Конфигурация работает, но рекомендуется проверить настройки")
        return True
    else:
        print("🎉 ВСЕ НАСТРОЙКИ ПРАВИЛЬНЫЕ!")
        print("🚀 Supabase готов к использованию")
        return True

if __name__ == "__main__":
    test_supabase_config()