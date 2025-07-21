#!/usr/bin/env python3
"""
Прямая настройка Supabase без зависимостей от других модулей
Создает таблицы и добавляет каналы напрямую
"""

import os
import sys

# EdTech каналы для добавления
EDTECH_CHANNELS = [
    {"username": "@edtexno", "display_name": "EdTechno", "priority": 10},
    {"username": "@vc_edtech", "display_name": "VC EdTech", "priority": 9},
    {"username": "@rusedweek", "display_name": "Russian EdWeek", "priority": 8},
    {"username": "@edtech_hub", "display_name": "EdTech Hub", "priority": 8},
    {"username": "@prosv_media", "display_name": "Просвещение Медиа", "priority": 7},
    {"username": "@digitaleducation", "display_name": "Цифровое образование", "priority": 7},
    {"username": "@skillfactory_news", "display_name": "SkillFactory News", "priority": 6},
    {"username": "@netology_ru", "display_name": "Нетология", "priority": 6},
    {"username": "@geekbrains_ru", "display_name": "GeekBrains", "priority": 6},
    {"username": "@skyengschool", "display_name": "Skyeng", "priority": 5}
]

def get_database_connection():
    """Получение прямого подключения к PostgreSQL"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Получение переменных окружения
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL не найден в переменных окружения")
            return None
        
        print(f"🔗 Подключаемся к PostgreSQL...")
        print(f"🔗 URL: {database_url[:50]}...")
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            connect_timeout=15
        )
        conn.autocommit = True
        
        # Тест подключения
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()['version']
        print(f"✅ Подключение успешно: {version[:50]}...")
        
        return conn
        
    except ImportError:
        print("❌ psycopg2 не установлен")
        return None
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return None

def create_tables(conn):
    """Создание всех таблиц"""
    try:
        cursor = conn.cursor()
        
        print("📊 Создание таблиц...")
        
        # Таблица каналов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT,
                priority INTEGER DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
                is_active BOOLEAN DEFAULT true,
                last_message_id BIGINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица channels создана")
        
        # Таблица обработанных сообщений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                id SERIAL PRIMARY KEY,
                channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
                message_id BIGINT NOT NULL,
                message_text TEXT,
                summary TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published BOOLEAN DEFAULT false,
                UNIQUE(channel_id, message_id)
            )
        """)
        print("✅ Таблица processed_messages создана")
        
        # Таблица настроек
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица settings создана")
        
        # Таблица логов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS run_logs (
                id SERIAL PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT CHECK (status IN ('started', 'completed', 'failed')),
                channels_processed INTEGER DEFAULT 0,
                messages_collected INTEGER DEFAULT 0,
                news_published INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)
        print("✅ Таблица run_logs создана")
        
        # Настройки по умолчанию
        default_settings = [
            ('max_news_count', '10', 'Максимальное количество новостей в дайджесте'),
            ('target_channel', '@vestnik_edtech', 'Целевой канал для публикации'),
            ('digest_times', '12:00,18:00', 'Время публикации дайджестов'),
            ('summary_max_length', '150', 'Максимальная длина суммаризации в символах'),
            ('hours_lookback', '12', 'Сколько часов назад искать новости'),
        ]
        
        for key, value, description in default_settings:
            cursor.execute("""
                INSERT INTO settings (key, value, description) 
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO NOTHING
            """, (key, value, description))
        
        print("✅ Настройки по умолчанию добавлены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def add_channels(conn):
    """Добавление EdTech каналов"""
    try:
        cursor = conn.cursor()
        
        print("📺 Добавление EdTech каналов...")
        
        added_count = 0
        for channel in EDTECH_CHANNELS:
            try:
                cursor.execute("""
                    INSERT INTO channels (username, display_name, priority)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        priority = EXCLUDED.priority,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (channel["username"], channel["display_name"], channel["priority"]))
                
                result = cursor.fetchone()
                if result:
                    added_count += 1
                    print(f"✅ {channel['display_name']} - добавлен/обновлен")
                
            except Exception as channel_error:
                print(f"⚠️ Ошибка с каналом {channel['username']}: {channel_error}")
        
        print(f"✅ Обработано каналов: {added_count}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка добавления каналов: {e}")
        return False

def verify_setup(conn):
    """Проверка настройки"""
    try:
        cursor = conn.cursor()
        
        print("\n🔍 Проверка настройки:")
        
        # Количество таблиц
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        print(f"📋 Таблицы: {', '.join(tables)}")
        
        # Количество каналов
        cursor.execute("SELECT COUNT(*) as count FROM channels")
        channels_count = cursor.fetchone()['count']
        print(f"📺 Каналов в базе: {channels_count}")
        
        # Количество настроек
        cursor.execute("SELECT COUNT(*) as count FROM settings")
        settings_count = cursor.fetchone()['count']
        print(f"⚙️ Настроек в базе: {settings_count}")
        
        if len(tables) >= 4 and channels_count > 0 and settings_count > 0:
            print("🎉 Supabase настроен успешно!")
            return True
        else:
            print("❌ Настройка неполная")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

def main():
    print("🐘 Прямая настройка Supabase для EdTech Bot")
    print("=" * 50)
    
    # Проверка переменных окружения
    required_vars = ['DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("💡 Установите их в Railway Dashboard")
        return 1
    
    # Подключение к базе
    conn = get_database_connection()
    if not conn:
        print("❌ Не удалось подключиться к базе данных")
        return 1
    
    try:
        # Создание таблиц
        if not create_tables(conn):
            print("❌ Ошибка создания таблиц")
            return 1
        
        # Добавление каналов
        if not add_channels(conn):
            print("❌ Ошибка добавления каналов")
            return 1
        
        # Проверка
        if not verify_setup(conn):
            print("❌ Ошибка проверки настройки")
            return 1
        
        print("\n🎉 НАСТРОЙКА SUPABASE ЗАВЕРШЕНА УСПЕШНО!")
        print("✅ База данных готова к использованию")
        print("✅ EdTech каналы добавлены")
        print("✅ Настройки применены")
        print("\n🚀 Можно запускать основное приложение")
        
        return 0
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())