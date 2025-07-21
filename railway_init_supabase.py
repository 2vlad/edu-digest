#!/usr/bin/env python3
"""
Скрипт для инициализации Supabase на Railway
Запуск: добавьте в Railway как одноразовую команду
"""

import sys
import os
sys.path.append('src')

# Этот скрипт запускается на Railway где есть переменные окружения
from force_supabase_init import force_create_supabase_tables, test_connection

if __name__ == "__main__":
    print("🚂 Railway Supabase Initialization")
    print("=" * 40)
    
    # Показываем переменные окружения (замаскированные)
    supabase_url = os.getenv('SUPABASE_URL', 'НЕ_НАЙДЕНО')
    database_url = os.getenv('DATABASE_URL', 'НЕ_НАЙДЕНО')
    
    print(f"SUPABASE_URL: {supabase_url[:30]}..." if supabase_url != 'НЕ_НАЙДЕНО' else "SUPABASE_URL: НЕ_НАЙДЕНО")
    print(f"DATABASE_URL: {database_url[:30]}..." if database_url != 'НЕ_НАЙДЕНО' else "DATABASE_URL: НЕ_НАЙДЕНО")
    print()
    
    if test_connection():
        print("🎯 Создаем таблицы в Supabase...")
        if force_create_supabase_tables():
            print("\n🎉 ГОТОВО! Supabase инициализирован")
            print("🔄 Перезапустите основное приложение")
            sys.exit(0)
        else:
            print("\n❌ Не удалось создать таблицы")
            sys.exit(1)
    else:
        print("❌ Подключение к Supabase не работает")
        print("📖 Проверьте настройки в Railway переменных")
        sys.exit(1)