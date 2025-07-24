#!/usr/bin/env python3
"""
Скрипт инициализации базы данных Supabase для EdTech News Digest Bot
ТОЛЬКО SUPABASE - БЕЗ SQLite FALLBACK
"""
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_database, test_db, ChannelsDB, SettingsDB

def main():
    """Основная функция инициализации"""
    print("🚀 Инициализация базы данных EdTech News Digest Bot (Supabase)")
    print("="*60)
    
    try:
        # Создание структуры базы данных
        print("\n1. Создание структуры базы данных...")
        init_database()
        print("✅ Структура базы данных создана")
        
        # Тестирование подключения
        print("\n2. Тестирование подключения...")
        if test_db():
            print("✅ Тестирование базы данных прошло успешно")
        else:
            print("❌ Ошибка при тестировании базы данных")
            sys.exit(1)
        
        # Добавление базовых настроек (они уже добавляются в init_database)
        print("\n3. Проверка настроек по умолчанию...")
        settings_to_check = ['max_news_count', 'target_channel', 'digest_times', 'hours_lookback']
        for setting_key in settings_to_check:
            value = SettingsDB.get_setting(setting_key)
            print(f"  ✅ {setting_key}: {value}")
        
        print("\n4. Состояние каналов...")
        channels = ChannelsDB.get_active_channels()
        if channels:
            print(f"  📺 Найдено {len(channels)} каналов:")
            for channel in channels[:5]:  # Показываем первые 5
                print(f"    - {channel['username']} (приоритет: {channel['priority']})")
        else:
            print("  ⚠️ Каналы не найдены. Добавьте каналы через админ-панель.")
        
        print("\n✅ Инициализация завершена успешно!")
        print("🌐 Для управления запустите админ-панель: python main.py admin")
        print("📡 Для сбора новостей: python main.py collect")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации: {e}")
        print("💡 Проверьте переменные окружения Supabase:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY") 
        print("   - DATABASE_URL")
        sys.exit(1)

if __name__ == "__main__":
    main() 