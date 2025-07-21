#!/usr/bin/env python3
"""
Скрипт инициализации базы данных для EdTech News Digest Bot
Согласно PRD - этап 1, критерий приёмки
"""
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_database, test_db, ChannelsDB, SettingsDB

def main():
    """Основная функция инициализации"""
    print("🚀 Инициализация базы данных EdTech News Digest Bot")
    print("="*50)
    
    try:
        # Создание структуры базы данных
        init_database()
        print("✅ Структура базы данных создана")
        
        # Тестирование подключения
        if test_db():
            print("✅ Тестирование базы данных прошло успешно")
        else:
            print("❌ Ошибка при тестировании базы данных")
            sys.exit(1)
        
        # Добавление тестовых каналов для демонстрации
        test_channels = [
            ("@vc_edtech", "VC EdTech News", 10),
            ("@rusedweek", "Russian EdWeek", 8),
            ("@edcrunch", "EdCrunch News", 7),
        ]
        
        print("\n📺 Добавление тестовых каналов:")
        for username, display_name, priority in test_channels:
            try:
                channel_id = ChannelsDB.add_channel(username, display_name, priority)
                print(f"✅ {display_name} ({username}) - приоритет {priority}")
            except Exception as e:
                if "уже существует" in str(e):
                    print(f"⚠️  {display_name} ({username}) - уже существует")
                else:
                    print(f"❌ Ошибка при добавлении {username}: {e}")
        
        # Проверка настроек по умолчанию
        print("\n⚙️  Настройки по умолчанию:")
        settings_to_check = ['max_news_count', 'target_channel', 'digest_times']
        for setting_key in settings_to_check:
            value = SettingsDB.get_setting(setting_key)
            print(f"  {setting_key}: {value}")
        
        print("\n✅ Инициализация завершена успешно!")
        print(f"📁 База данных создана: data/edu_digest.db")
        print("🔄 Для проверки запустите: python -c \"from src.database import test_db; print('OK' if test_db() else 'ERROR')\"")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()