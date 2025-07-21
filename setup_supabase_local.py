#!/usr/bin/env python3
"""
Автоматическая настройка Supabase для локального тестирования
"""

import sys
import os
sys.path.append('src')

def main():
    print("🔧 АВТОМАТИЧЕСКАЯ НАСТРОЙКА SUPABASE")
    print("=" * 50)
    
    # Шаг 1: Проверяем текущую конфигурацию
    print("1️⃣ Проверка текущей конфигурации...")
    
    try:
        from src.config import DATABASE_URL, SUPABASE_URL, SUPABASE_KEY
        
        needs_setup = (
            not SUPABASE_URL or "your-project-ref" in SUPABASE_URL or
            not SUPABASE_KEY or "your-anon-public" in SUPABASE_KEY or  
            not DATABASE_URL or "your-password" in DATABASE_URL
        )
        
        if not needs_setup:
            print("✅ Supabase уже настроен!")
            print(f"📊 URL: {SUPABASE_URL}")
            print(f"🔑 Key: {SUPABASE_KEY[:20]}...")
            
            # Тестируем подключение
            print("\n2️⃣ Тестирование подключения...")
            try:
                # Прямое подключение к Supabase
                result = test_supabase_connection()
                if result:
                    print("✅ Подключение к Supabase работает!")
                    
                    # Создаем таблицы
                    print("\n3️⃣ Инициализация таблиц...")
                    setup_result = setup_supabase_tables()
                    if setup_result:
                        print("✅ Таблицы созданы успешно!")
                        return True
                    else:
                        print("❌ Ошибка создания таблиц")
                        return False
                else:
                    print("❌ Подключение к Supabase не работает")
                    return False
                    
            except Exception as e:
                print(f"❌ Ошибка тестирования: {e}")
                return False
        else:
            print("❌ Supabase не настроен в .env файле")
            print("\n📋 ИНСТРУКЦИИ ПО НАСТРОЙКЕ:")
            print_setup_instructions()
            return False
            
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False

def test_supabase_connection():
    """Тестирование подключения к Supabase"""
    try:
        # Используем наш готовый модуль
        from src.supabase_db import supabase_db
        
        if supabase_db.initialize():
            print("✅ Supabase инициализирован")
            
            # Тест подключения
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()['version']
            print(f"✅ PostgreSQL версия: {version[:50]}...")
            
            return True
        else:
            print("❌ Не удалось инициализировать Supabase")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования подключения: {e}")
        return False

def setup_supabase_tables():
    """Создание таблиц в Supabase"""
    try:
        from src.supabase_db import init_supabase_database
        
        print("🗃️ Создание таблиц в Supabase...")
        result = init_supabase_database()
        
        if result:
            print("✅ Все таблицы созданы:")
            print("   - channels (отслеживаемые каналы)")
            print("   - processed_messages (обработанные сообщения)")
            print("   - settings (настройки системы)")
            print("   - run_logs (логи запусков)")
            
            # Добавляем EdTech каналы
            print("\n📺 Добавление EdTech каналов...")
            add_edtech_channels()
            
            return True
        else:
            print("❌ Ошибка создания таблиц")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка настройки таблиц: {e}")
        import traceback
        print(f"📋 Детали: {traceback.format_exc()}")
        return False

def add_edtech_channels():
    """Добавление EdTech каналов"""
    try:
        from src.supabase_db import SupabaseChannelsDB
        
        channels = [
            ("@edtexno", "EdTechno", 10),
            ("@vc_edtech", "VC EdTech", 9), 
            ("@rusedweek", "Russian EdWeek", 8),
            ("@edtech_hub", "EdTech Hub", 8),
            ("@prosv_media", "Просвещение Медиа", 7),
            ("@digitaleducation", "Цифровое образование", 7),
            ("@skillfactory_news", "SkillFactory News", 6),
            ("@netology_ru", "Нетология", 6),
            ("@geekbrains_ru", "GeekBrains", 6),
            ("@skyengschool", "Skyeng", 5)
        ]
        
        added_count = 0
        for username, display_name, priority in channels:
            try:
                channel_id = SupabaseChannelsDB.add_channel(username, display_name, priority)
                print(f"✅ {display_name} (ID: {channel_id})")
                added_count += 1
            except Exception as e:
                if "уже существует" in str(e) or "duplicate key" in str(e):
                    print(f"ℹ️ {display_name} - уже существует")
                else:
                    print(f"❌ {display_name} - ошибка: {e}")
        
        print(f"✅ Добавлено каналов: {added_count}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка добавления каналов: {e}")
        return False

def print_setup_instructions():
    """Печатает инструкции по настройке"""
    print("""
🔧 НАСТРОЙКА SUPABASE:

1️⃣ Создайте проект:
   • Перейдите на https://supabase.com
   • Нажмите "New project"
   • Выберите организацию
   • Введите название: "EdTech News Digest"  
   • Выберите регион (Europe для лучшей скорости)
   • Создайте надежный пароль
   • Нажмите "Create new project"

2️⃣ Получите API ключи:
   • В левом меню выберите Settings → API
   • Скопируйте Project URL
   • Скопируйте anon public key

3️⃣ Получите Database URL:
   • В левом меню выберите Settings → Database
   • Найдите "Connection string"
   • Выберите "URI" 
   • Скопируйте строку подключения

4️⃣ Обновите .env файл:
   • Замените SUPABASE_URL на ваш Project URL
   • Замените SUPABASE_ANON_KEY на ваш anon public key  
   • Замените DATABASE_URL на вашу строку подключения

5️⃣ Запустите настройку:
   python setup_supabase_local.py

📋 Пример .env:
SUPABASE_URL="https://abcdefgh.supabase.co"
SUPABASE_ANON_KEY="eyJ0eXAiOiJKV1QiLCJhbGc..."
DATABASE_URL="postgresql://postgres:your_password@db.abcdefgh.supabase.co:5432/postgres"
""")

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 SUPABASE НАСТРОЕН УСПЕШНО!")
        print("✅ Можете запускать: python test_local_supabase.py")
    else:
        print("\n❌ НАСТРОЙКА НЕ ЗАВЕРШЕНА")
        print("💡 Следуйте инструкциям выше для настройки Supabase")