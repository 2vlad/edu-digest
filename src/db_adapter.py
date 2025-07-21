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
            init_supabase_database as init_database,
            test_supabase_db as test_db,
            SupabaseChannelsDB as ChannelsDB,
            SupabaseSettingsDB as SettingsDB,
            SupabaseProcessedMessagesDB as ProcessedMessagesDB,
            supabase_db
        )
        
        def create_connection():
            """Получение подключения для Supabase"""
            if not supabase_db.initialized:
                supabase_db.initialize()
            return supabase_db.get_connection()
            
    except ImportError as e:
        logger.warning(f"⚠️ Не удалось импортировать Supabase модули: {e}")
        logger.info("📦 Fallback to SQLite")
        USE_SUPABASE = False

if not USE_SUPABASE:
    logger.info("📁 Using SQLite fallback")
    from .database import (
        init_database,
        test_db,
        ChannelsDB,
        SettingsDB,
        ProcessedMessagesDB,
        create_connection,
        DATABASE_PATH
    )

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
    if USE_SUPABASE:
        return {
            'type': 'PostgreSQL (Supabase)',
            'url': DATABASE_URL or SUPABASE_URL,
            'persistent': True,
            'railway_compatible': True
        }
    else:
        return {
            'type': 'SQLite',
            'path': DATABASE_PATH,
            'persistent': DATABASE_PATH and '/data/' in DATABASE_PATH if DATABASE_PATH else False,
            'railway_compatible': False
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