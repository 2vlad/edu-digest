#!/usr/bin/env python3
"""
Адаптер базы данных - автоматически выбирает между SQLite и Supabase
"""

import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

# Определяем какую БД использовать
try:
    from .config import DATABASE_URL, SUPABASE_URL, DATABASE_PATH
except ImportError:
    from config import DATABASE_URL, SUPABASE_URL, DATABASE_PATH

USE_SUPABASE = bool(DATABASE_URL or SUPABASE_URL)

if USE_SUPABASE:
    logger.info("🐘 Using Supabase PostgreSQL")
    try:
        from .supabase_db import (
            init_supabase_database as _init_supabase_database,
            test_supabase_db as _test_supabase_db,
            SupabaseChannelsDB as ChannelsDB,
            SupabaseSettingsDB as SettingsDB,
            SupabaseProcessedMessagesDB as ProcessedMessagesDB,
            supabase_db
        )
        
        def create_connection():
            """Получение подключения для Supabase с автоматическим fallback"""
            try:
                if not supabase_db.initialized:
                    if not supabase_db.initialize():
                        raise Exception("Supabase initialization failed")
                return supabase_db.get_connection()
            except Exception as e:
                logger.error(f"❌ Supabase connection failed: {e}")
                logger.info("🔄 Switching to SQLite fallback...")
                # Переключаемся на SQLite
                _switch_to_sqlite_fallback()
                return _sqlite_create_connection()
        
        def init_database():
            """Инициализация БД с fallback на SQLite"""
            try:
                return _init_supabase_database()
            except Exception as e:
                logger.error(f"❌ Supabase database init failed: {e}")
                logger.info("🔄 Switching to SQLite fallback...")
                _switch_to_sqlite_fallback()
                return _sqlite_init_database()
        
        def test_db():
            """Тестирование БД с fallback на SQLite"""
            try:
                return _test_supabase_db()
            except Exception as e:
                logger.error(f"❌ Supabase test failed: {e}")
                logger.info("🔄 Switching to SQLite fallback...")
                _switch_to_sqlite_fallback()
                return _sqlite_test_db()
                
    except ImportError as e:
        logger.warning(f"⚠️ Не удалось импортировать Supabase модули: {e}")
        logger.info("📦 Fallback to SQLite")
        USE_SUPABASE = False

# Импортируем SQLite функции для fallback
try:
    from .database import (
        init_database as _sqlite_init_database,
        test_db as _sqlite_test_db,
        ChannelsDB as _SQLiteChannelsDB,
        SettingsDB as _SQLiteSettingsDB,
        ProcessedMessagesDB as _SQLiteProcessedMessagesDB,
        create_connection as _sqlite_create_connection,
        DATABASE_PATH
    )
except ImportError:
    from database import (
        init_database as _sqlite_init_database,
        test_db as _sqlite_test_db,
        ChannelsDB as _SQLiteChannelsDB,
        SettingsDB as _SQLiteSettingsDB,
        ProcessedMessagesDB as _SQLiteProcessedMessagesDB,
        create_connection as _sqlite_create_connection,
        DATABASE_PATH
    )

def _switch_to_sqlite_fallback():
    """Переключение на SQLite fallback во время выполнения"""
    global USE_SUPABASE, ChannelsDB, SettingsDB, ProcessedMessagesDB, init_database, test_db, create_connection
    USE_SUPABASE = False
    ChannelsDB = _SQLiteChannelsDB
    SettingsDB = _SQLiteSettingsDB 
    ProcessedMessagesDB = _SQLiteProcessedMessagesDB
    init_database = _sqlite_init_database
    test_db = _sqlite_test_db
    create_connection = _sqlite_create_connection
    logger.info("✅ Switched to SQLite fallback")

if not USE_SUPABASE:
    logger.info("📁 Using SQLite fallback")
    ChannelsDB = _SQLiteChannelsDB
    SettingsDB = _SQLiteSettingsDB
    ProcessedMessagesDB = _SQLiteProcessedMessagesDB
    init_database = _sqlite_init_database
    test_db = _sqlite_test_db
    create_connection = _sqlite_create_connection

# Экспортируем все необходимые функции и классы
__all__ = [
    'init_database',
    'test_db', 
    'ChannelsDB',
    'SettingsDB',
    'ProcessedMessagesDB',
    'create_connection',
    'USE_SUPABASE'
]

def get_database_info() -> Dict[str, Any]:
    """Возвращает информацию о текущей базе данных"""
    global USE_SUPABASE
    if USE_SUPABASE:
        return {
            'type': 'PostgreSQL (Supabase)',
            'url': DATABASE_URL or SUPABASE_URL,
            'persistent': True,
            'railway_compatible': True,
            'fallback_available': True
        }
    else:
        return {
            'type': 'SQLite',
            'path': DATABASE_PATH,
            'persistent': DATABASE_PATH and '/data/' in DATABASE_PATH if DATABASE_PATH else False,
            'railway_compatible': False,
            'fallback_available': False
        }

if __name__ == "__main__":
    # Тестирование адаптера
    db_info = get_database_info()
    print(f"🗄️ Database info: {db_info}")
    
    try:
        init_database()
        print("✅ Database initialized successfully!")
        
        if test_db():
            print("✅ Database test passed!")
        else:
            print("❌ Database test failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")