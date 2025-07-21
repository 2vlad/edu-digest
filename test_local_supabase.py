#!/usr/bin/env python3
"""
Локальное тестирование с Supabase
Проверяет подключение и инициализирует систему
"""

import sys
import os
import asyncio
sys.path.append('src')

def main():
    print("🧪 ЛОКАЛЬНОЕ ТЕСТИРОВАНИЕ С SUPABASE")
    print("=" * 60)
    
    # Шаг 1: Проверяем конфигурацию
    print("1️⃣ ПРОВЕРКА КОНФИГУРАЦИИ")
    print("-" * 30)
    
    try:
        from src.config import (DATABASE_URL, SUPABASE_URL, SUPABASE_KEY, 
                               TELEGRAM_API_ID, TELEGRAM_API_HASH, ANTHROPIC_API_KEY)
        
        config_status = {
            "SUPABASE_URL": "✅ OK" if SUPABASE_URL and "your-project-ref" not in SUPABASE_URL else "❌ Needs setup",
            "SUPABASE_ANON_KEY": "✅ OK" if SUPABASE_KEY and "your-anon-public" not in SUPABASE_KEY else "❌ Needs setup", 
            "DATABASE_URL": "✅ OK" if DATABASE_URL and "your-password" not in DATABASE_URL else "❌ Needs setup",
            "TELEGRAM_API_ID": "✅ OK" if TELEGRAM_API_ID else "❌ Missing",
            "TELEGRAM_API_HASH": "✅ OK" if TELEGRAM_API_HASH else "❌ Missing",
            "ANTHROPIC_API_KEY": "✅ OK" if ANTHROPIC_API_KEY else "❌ Missing"
        }
        
        for key, status in config_status.items():
            print(f"   {key}: {status}")
        
        missing_config = [k for k, v in config_status.items() if "❌" in v]
        if missing_config:
            print(f"\n❌ КОНФИГУРАЦИЯ НЕ ГОТОВА!")
            print(f"Необходимо настроить: {', '.join(missing_config)}")
            print("\n📋 ЧТО ДЕЛАТЬ:")
            
            if any("SUPABASE" in key or "DATABASE" in key for key in missing_config):
                print("🔧 НАСТРОЙКА SUPABASE:")
                print("1. Перейдите на https://supabase.com")
                print("2. Создайте новый проект")
                print("3. В Settings -> API скопируйте:")
                print("   - Project URL (SUPABASE_URL)")
                print("   - anon public key (SUPABASE_ANON_KEY)")
                print("4. В Settings -> Database скопируйте:")
                print("   - Connection string (DATABASE_URL)")
                print("5. Обновите .env файл с реальными значениями")
                
            return False
        else:
            print("✅ Конфигурация готова!")
            
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False
    
    # Шаг 2: Тестируем подключение к базе данных
    print("\n2️⃣ ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ")
    print("-" * 30)
    
    try:
        from src.db_adapter import init_database, test_db, get_database_info, ChannelsDB
        
        # Получаем информацию о базе
        db_info = get_database_info()
        print(f"📊 База данных: {db_info['type']}")
        
        if not db_info.get('production_ready', False):
            print("⚠️ ВНИМАНИЕ: Используется SQLite fallback!")
            print("💡 Настройте Supabase для полного тестирования")
            
        # Инициализируем базу данных
        print("🔧 Инициализация базы данных...")
        init_database()
        print("✅ База данных инициализирована")
        
        # Тестируем подключение
        print("🧪 Тестирование подключения...")
        if test_db():
            print("✅ Тест базы данных прошел успешно")
        else:
            print("❌ Тест базы данных не прошел")
            return False
            
        # Проверяем каналы
        print("📺 Проверка каналов...")
        channels = ChannelsDB.get_active_channels()
        print(f"✅ Найдено каналов: {len(channels)}")
        
        if len(channels) == 0:
            print("⚙️ Добавляем тестовые каналы...")
            test_channels = [
                ("@edtexno", "EdTechno", 10),
                ("@vc_edtech", "VC EdTech", 9),
                ("@rusedweek", "Russian EdWeek", 8),
            ]
            
            for username, display_name, priority in test_channels:
                try:
                    channel_id = ChannelsDB.add_channel(username, display_name, priority)
                    print(f"✅ Добавлен канал: {display_name} (ID: {channel_id})")
                except Exception as e:
                    if "уже существует" in str(e) or "already exists" in str(e):
                        print(f"ℹ️ Канал {display_name} уже существует")
                    else:
                        print(f"❌ Ошибка добавления {display_name}: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка работы с базой данных: {e}")
        import traceback
        print(f"📋 Детали: {traceback.format_exc()}")
        return False
    
    # Шаг 3: Тестируем Telegram API
    print("\n3️⃣ ТЕСТИРОВАНИЕ TELEGRAM API")
    print("-" * 30)
    
    try:
        print("📡 Тестирование подключения к Telegram...")
        # Импортируем и тестируем Telegram reader
        from src.telegram_reader import TelegramChannelReader
        
        reader = TelegramChannelReader()
        
        # Пытаемся инициализировать (но не асинхронно для простоты)
        print("✅ Telegram модуль импортирован")
        print("💡 Полное тестирование Telegram требует async окружения")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования Telegram: {e}")
    
    # Шаг 4: Тестируем Claude API 
    print("\n4️⃣ ТЕСТИРОВАНИЕ CLAUDE API")
    print("-" * 30)
    
    try:
        from src.claude_summarizer import ClaudeSummarizer
        
        summarizer = ClaudeSummarizer()
        print("✅ Claude модуль инициализирован")
        
        # Простой тест соединения
        test_result = summarizer.test_api_connection()
        if test_result.get('success', False):
            print("✅ Claude API тест прошел успешно")
        else:
            print(f"❌ Claude API тест не прошел: {test_result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования Claude: {e}")
    
    # Шаг 5: Запуск админ-панели
    print("\n5️⃣ ЗАПУСК АДМИН-ПАНЕЛИ")
    print("-" * 30)
    print("🌐 Запуск Flask админ-панели для тестирования...")
    print("📍 Откройте http://localhost:5002 в браузере")
    print("⚠️ Нажмите Ctrl+C чтобы остановить сервер")
    
    try:
        from src.admin_panel import app
        from src.config import FLASK_PORT
        
        app.run(host='127.0.0.1', port=FLASK_PORT, debug=True)
        
    except KeyboardInterrupt:
        print("\n✅ Тестирование завершено пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска админ-панели: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ЛОКАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    else:
        print("\n❌ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО - ИСПРАВЬТЕ ОШИБКИ")
        sys.exit(1)