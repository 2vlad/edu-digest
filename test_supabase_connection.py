#!/usr/bin/env python3
"""
Простой тест подключения к Supabase без зависимостей от проекта
"""

import os
import sys

def test_connection():
    """Тест подключения к Supabase PostgreSQL"""
    print("🔧 Тест подключения к Supabase")
    print("=" * 40)
    
    # Проверка переменных окружения
    database_url = os.getenv('DATABASE_URL')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"🔗 DATABASE_URL: {'✅ Найден' if database_url else '❌ Отсутствует'}")
    print(f"🔗 SUPABASE_URL: {'✅ Найден' if supabase_url else '❌ Отсутствует'}")
    print(f"🔑 SUPABASE_ANON_KEY: {'✅ Найден' if supabase_key else '❌ Отсутствует'}")
    
    if not database_url:
        print("\n❌ DATABASE_URL не найден")
        print("💡 Добавьте в Railway переменную DATABASE_URL с PostgreSQL строкой подключения")
        return False
    
    if not supabase_url:
        print("\n❌ SUPABASE_URL не найден")
        print("💡 Добавьте в Railway переменную SUPABASE_URL с URL вашего Supabase проекта")
        return False
        
    if not supabase_key:
        print("\n❌ SUPABASE_ANON_KEY не найден")
        print("💡 Добавьте в Railway переменную SUPABASE_ANON_KEY с анонимным ключом")
        return False
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        print(f"\n🔗 Подключаемся к PostgreSQL...")
        print(f"🌍 URL: {database_url[:30]}...")
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version_info = cursor.fetchone()['version']
        
        print(f"✅ Подключение успешно!")
        print(f"🐘 PostgreSQL: {version_info[:80]}...")
        
        # Проверка существующих таблиц
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        print(f"📋 Существующие таблицы ({len(tables)}): {', '.join(tables) if tables else 'Нет таблиц'}")
        
        # Если есть таблица channels, проверим количество записей
        if 'channels' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM channels")
            channels_count = cursor.fetchone()['count']
            print(f"📺 Каналов в базе: {channels_count}")
        
        conn.close()
        print("\n🎉 ТЕСТ ПРОШЕЛ УСПЕШНО!")
        print("✅ Supabase PostgreSQL доступен и готов к использованию")
        
        return True
        
    except ImportError:
        print("\n❌ psycopg2 не найден")
        print("💡 Установите зависимости: pip install psycopg2-binary")
        return False
        
    except Exception as e:
        print(f"\n❌ Ошибка подключения: {e}")
        
        if "Network is unreachable" in str(e):
            print("🌐 Проблема с сетью - Railway не может подключиться к Supabase")
            print("💡 Проверьте настройки DATABASE_URL в Supabase Dashboard")
            
        elif "authentication failed" in str(e):
            print("🔑 Проблема с аутентификацией")
            print("💡 Проверьте корректность DATABASE_URL строки подключения")
            
        elif "timeout" in str(e):
            print("⏰ Таймаут подключения")
            print("💡 Возможно Supabase временно недоступен")
            
        else:
            print("🔧 Общая ошибка подключения к базе данных")
            
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)