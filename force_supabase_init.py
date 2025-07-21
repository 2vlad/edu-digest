#!/usr/bin/env python3
"""
Принудительная инициализация Supabase базы данных
Создает таблицы в Supabase даже при проблемах с подключением
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def force_create_supabase_tables():
    """Принудительное создание таблиц в Supabase"""
    
    # Получаем DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL не найден в переменных окружения")
        return False
    
    print(f"🔗 Подключаемся к: {database_url[:50]}...")
    
    try:
        # Подключение с расширенными настройками
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            connect_timeout=30,
            application_name="edu_digest_init"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Подключение установлено")
        
        # Создаем таблицы
        print("📊 Создание таблиц...")
        
        # 1. Таблица каналов
        cursor.execute('''
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
        ''')
        print("✅ Таблица channels создана")
        
        # 2. Таблица обработанных сообщений
        cursor.execute('''
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
        ''')
        print("✅ Таблица processed_messages создана")
        
        # 3. Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Таблица settings создана")
        
        # 4. Таблица логов
        cursor.execute('''
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
        ''')
        print("✅ Таблица run_logs создана")
        
        # 5. Вставка настроек по умолчанию
        default_settings = [
            ('max_news_count', '10', 'Максимальное количество новостей в дайджесте'),
            ('target_channel', '@vestnik_edtech', 'Целевой канал для публикации'),
            ('digest_times', '12:00,18:00', 'Время публикации дайджестов'),
            ('summary_max_length', '150', 'Максимальная длина суммаризации в символах'),
            ('hours_lookback', '12', 'Сколько часов назад искать новости'),
        ]
        
        for key, value, description in default_settings:
            cursor.execute('''
                INSERT INTO settings (key, value, description) 
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO NOTHING
            ''', (key, value, description))
        
        print("✅ Настройки по умолчанию добавлены")
        
        # 6. Проверим созданные таблицы
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        print(f"📋 Созданные таблицы: {', '.join(tables)}")
        
        # 7. Проверим настройки
        cursor.execute("SELECT COUNT(*) as count FROM settings")
        settings_count = cursor.fetchone()['count']
        print(f"⚙️ Настроек в базе: {settings_count}")
        
        conn.close()
        print("🎉 Supabase база данных успешно инициализирована!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации Supabase: {e}")
        
        # Дополнительная диагностика
        if "Network is unreachable" in str(e):
            print("🌐 Сетевая проблема - возможно:")
            print("   - Railway не может достучаться до Supabase")
            print("   - Неправильный регион Supabase")
            print("   - Проблемы с DNS")
        elif "authentication failed" in str(e):
            print("🔑 Проблема с аутентификацией:")
            print("   - Проверьте пароль в DATABASE_URL")
            print("   - Проверьте права доступа пользователя")
        elif "does not exist" in str(e):
            print("🗄️ Проблема с базой данных:")
            print("   - Проверьте название базы в DATABASE_URL")
            print("   - Убедитесь что база данных создана в Supabase")
        
        return False

def test_connection():
    """Тестирование подключения к Supabase"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL не найден")
        return False
    
    print("🧪 Тестирование подключения к Supabase...")
    
    try:
        conn = psycopg2.connect(database_url, connect_timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Подключение работает!")
        print(f"📍 PostgreSQL версия: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Подключение не работает: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Принудительная инициализация Supabase")
    print("=" * 50)
    
    # Сначала тестируем подключение
    if test_connection():
        print("\n" + "=" * 50)
        # Если подключение работает, создаем таблицы
        if force_create_supabase_tables():
            print("\n🎯 Готово! Теперь перезапустите приложение на Railway")
        else:
            print("\n❌ Инициализация не удалась")
    else:
        print("\n❌ Нет подключения к Supabase")
        print("💡 Проверьте переменные окружения:")
        print("   - DATABASE_URL должен быть правильным")
        print("   - Supabase проект должен быть запущен")
        print("   - Настройки сети должны разрешать подключение")