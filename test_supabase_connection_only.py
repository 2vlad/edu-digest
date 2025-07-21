#!/usr/bin/env python3
"""
Быстрый тест подключения к Supabase
"""

import sys
sys.path.append('src')

def main():
    print("🧪 БЫСТРЫЙ ТЕСТ SUPABASE ПОДКЛЮЧЕНИЯ")
    print("=" * 50)
    
    try:
        # Загружаем конфигурацию
        print("1️⃣ Загрузка конфигурации...")
        from src.config import DATABASE_URL, SUPABASE_URL, SUPABASE_KEY
        
        # Проверяем что это не placeholder'ы
        if 'your-project-ref' in SUPABASE_URL:
            print("❌ SUPABASE_URL содержит placeholder")
            print("💡 Запустите: python configure_supabase_interactive.py")
            return False
            
        if 'your-anon-public' in SUPABASE_KEY:
            print("❌ SUPABASE_ANON_KEY содержит placeholder")
            print("💡 Запустите: python configure_supabase_interactive.py")
            return False
            
        if 'your-password' in DATABASE_URL:
            print("❌ DATABASE_URL содержит placeholder") 
            print("💡 Запустите: python configure_supabase_interactive.py")
            return False
        
        print(f"✅ URL: {SUPABASE_URL}")
        print(f"✅ Key: {SUPABASE_KEY[:20]}...")
        print(f"✅ DB: {DATABASE_URL[:30]}...")
        
        # Прямой тест подключения
        print("\n2️⃣ Тестирование PostgreSQL подключения...")
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()['version']
        
        print(f"✅ PostgreSQL подключение работает!")
        print(f"🐘 Версия: {version[:60]}...")
        
        # Проверяем таблицы
        print("\n3️⃣ Проверка существующих таблиц...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = [row['table_name'] for row in cursor.fetchall()]
        if tables:
            print(f"✅ Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"   📋 {table}")
        else:
            print("ℹ️ Таблицы не найдены - нужна инициализация")
            print("💡 Запустите: python setup_supabase_local.py")
        
        conn.close()
        
        print("\n🎉 SUPABASE ПОДКЛЮЧЕНИЕ РАБОТАЕТ!")
        return True
        
    except psycopg2.OperationalError as db_error:
        print(f"\n❌ Ошибка подключения к PostgreSQL: {db_error}")
        
        if "authentication failed" in str(db_error).lower():
            print("🔑 Проблема с аутентификацией")
            print("💡 Проверьте правильность пароля в DATABASE_URL")
        elif "connection refused" in str(db_error).lower():
            print("🌐 Проблема с подключением") 
            print("💡 Проверьте доступность Supabase сервера")
        elif "timeout" in str(db_error).lower():
            print("⏰ Таймаут подключения")
            print("💡 Проверьте интернет соединение")
        else:
            print("💡 Проверьте корректность DATABASE_URL")
            
        return False
        
    except ImportError as import_error:
        print(f"❌ Ошибка импорта: {import_error}")
        print("💡 Установите зависимости: pip install psycopg2-binary")
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        print(f"📋 Детали: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Подключение к Supabase готово!")
        print("🚀 Можете запускать: python test_local_supabase.py")
    else:
        print("\n❌ Подключение не работает")
        print("🔧 Исправьте проблемы выше")