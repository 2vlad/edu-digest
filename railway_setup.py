#!/usr/bin/env python3
"""
Полная настройка системы на Railway
Инициализирует либо Supabase, либо SQLite и добавляет каналы
"""

import sys
import os

# Добавляем src в путь
sys.path.append('src')
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🚂 Railway Setup для EdTech News Bot")
    print("=" * 50)
    
    # Определяем какую БД используем
    database_url = os.getenv('DATABASE_URL')
    supabase_url = os.getenv('SUPABASE_URL')
    
    if database_url and supabase_url:
        print("🐘 Обнаружены настройки Supabase - пытаемся настроить PostgreSQL")
        try:
            from force_supabase_init import force_create_supabase_tables, test_connection
            
            if test_connection():
                print("✅ Подключение к Supabase работает")
                if force_create_supabase_tables():
                    print("✅ Таблицы Supabase созданы")
                    setup_success = True
                else:
                    print("❌ Ошибка создания таблиц Supabase")
                    print("🔄 Переключаемся на SQLite fallback")
                    setup_success = False
            else:
                print("❌ Подключение к Supabase не работает")
                print("🔄 Используем SQLite fallback")
                setup_success = False
        except Exception as e:
            print(f"❌ Ошибка настройки Supabase: {e}")
            print("🔄 Используем SQLite fallback")
            setup_success = False
    else:
        print("📁 Настройки Supabase не найдены - используем SQLite")
        setup_success = False
    
    # Настраиваем каналы
    print("\n" + "=" * 30)
    print("📺 Настройка EdTech каналов")
    print("=" * 30)
    
    try:
        from setup_channels import setup_edtech_channels
        
        channels_success = setup_edtech_channels()
        
        if channels_success:
            print("✅ Каналы настроены успешно")
        else:
            print("❌ Ошибка настройки каналов")
            
    except Exception as e:
        print(f"❌ Критическая ошибка настройки каналов: {e}")
        import traceback
        traceback.print_exc()
        channels_success = False
    
    # Итоговый статус
    print("\n" + "=" * 50)
    if channels_success:
        print("🎉 RAILWAY SETUP ЗАВЕРШЕН УСПЕШНО!")
        print("💡 Система готова к работе:")
        print("   - База данных инициализирована")
        print("   - EdTech каналы добавлены") 
        print("   - Готово к сбору новостей")
        print("\n🔄 Перезапустите основное приложение")
        return 0
    else:
        print("❌ ОШИБКА RAILWAY SETUP")
        print("🔧 Проверьте логи и переменные окружения")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)