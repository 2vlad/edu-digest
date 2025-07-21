#!/usr/bin/env python3
"""
Адаптер базы данных - PostgreSQL первичная, SQLite fallback
Показывает четкие ошибки если PostgreSQL не настроен
"""

import logging
import os
from typing import List, Dict, Optional, Any

# Настройка детального логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_adapter.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Initializing DB Adapter - Production Mode")

# Импортируем конфигурацию
try:
    from .config import DATABASE_URL, SUPABASE_URL, SUPABASE_KEY
    logger.info("✅ Config imported from .config")
except ImportError:
    logger.info("🔄 Fallback to config import")
    try:
        from config import DATABASE_URL, SUPABASE_URL, SUPABASE_KEY
        logger.info("✅ Config imported from config")
    except ImportError as e:
        logger.error(f"❌ Failed to import config: {e}")
        DATABASE_URL = None
        SUPABASE_URL = None
        SUPABASE_KEY = None

# Проверяем переменные окружения
logger.info(f"🔍 Environment check:")
logger.info(f"   DATABASE_URL: {'✅ Set' if DATABASE_URL else '❌ Missing'}")
logger.info(f"   SUPABASE_URL: {'✅ Set' if SUPABASE_URL else '❌ Missing'}")
logger.info(f"   SUPABASE_KEY: {'✅ Set' if SUPABASE_KEY else '❌ Missing'}")

# Определяем доступность PostgreSQL
has_postgres_config = bool(DATABASE_URL or (SUPABASE_URL and SUPABASE_KEY))

if has_postgres_config:
    logger.info("✅ PostgreSQL configuration found - attempting to use Supabase")
    try:
        # Импортируем PostgreSQL модули
        try:
            from .supabase_db import (
                init_supabase_database,
                test_supabase_db,
                SupabaseChannelsDB,
                SupabaseSettingsDB,
                SupabaseProcessedMessagesDB,
                supabase_db
            )
            logger.info("✅ PostgreSQL modules imported successfully")
        except ImportError:
            from supabase_db import (
                init_supabase_database,
                test_supabase_db,
                SupabaseChannelsDB,
                SupabaseSettingsDB,
                SupabaseProcessedMessagesDB,
                supabase_db
            )
            logger.info("✅ PostgreSQL modules imported via fallback")
        
        # Используем PostgreSQL классы с логированием
        class LoggedChannelsDB:
            @staticmethod
            def add_channel(username: str, display_name: str = None, priority: int = 0) -> int:
                logger.debug(f"🔵 PostgreSQL: add_channel({username}, {display_name}, {priority})")
                try:
                    result = SupabaseChannelsDB.add_channel(username, display_name, priority)
                    logger.info(f"✅ Channel added: {username} -> ID {result}")
                    return result
                except Exception as e:
                    logger.error(f"❌ PostgreSQL add_channel failed: {e}")
                    raise
                    
            @staticmethod
            def get_active_channels():
                logger.debug("🔵 PostgreSQL: get_active_channels()")
                try:
                    result = SupabaseChannelsDB.get_active_channels()
                    logger.info(f"✅ Retrieved {len(result)} channels")
                    return result
                except Exception as e:
                    logger.error(f"❌ PostgreSQL get_active_channels failed: {e}")
                    raise
                    
            @staticmethod
            def update_last_message_id(channel_id: int, message_id: int):
                logger.debug(f"🔵 PostgreSQL: update_last_message_id({channel_id}, {message_id})")
                try:
                    result = SupabaseChannelsDB.update_last_message_id(channel_id, message_id)
                    logger.info(f"✅ Updated last message ID for channel {channel_id}")
                    return result
                except Exception as e:
                    logger.error(f"❌ PostgreSQL update_last_message_id failed: {e}")
                    raise
        
        class LoggedSettingsDB:
            @staticmethod
            def get_setting(key: str, default: str = None):
                logger.debug(f"🔵 PostgreSQL: get_setting({key})")
                try:
                    result = SupabaseSettingsDB.get_setting(key, default)
                    logger.debug(f"✅ Setting: {key} = {result}")
                    return result
                except Exception as e:
                    logger.error(f"❌ PostgreSQL get_setting failed: {e}")
                    raise
                    
            @staticmethod
            def set_setting(key: str, value: str, description: str = None):
                logger.debug(f"🔵 PostgreSQL: set_setting({key}, {value})")
                try:
                    result = SupabaseSettingsDB.set_setting(key, value, description)
                    logger.info(f"✅ Setting updated: {key} = {value}")
                    return result
                except Exception as e:
                    logger.error(f"❌ PostgreSQL set_setting failed: {e}")
                    raise
        
        class LoggedProcessedMessagesDB:
            @staticmethod
            def is_message_processed(channel_id: int, message_id: int) -> bool:
                logger.debug(f"🔵 PostgreSQL: is_message_processed({channel_id}, {message_id})")
                try:
                    result = SupabaseProcessedMessagesDB.is_message_processed(channel_id, message_id)
                    return result
                except Exception as e:
                    logger.error(f"❌ PostgreSQL is_message_processed failed: {e}")
                    raise
                    
            @staticmethod
            def mark_message_processed(channel_id: int, message_id: int, message_text: str = None, summary: str = None) -> int:
                logger.debug(f"🔵 PostgreSQL: mark_message_processed({channel_id}, {message_id})")
                try:
                    result = SupabaseProcessedMessagesDB.mark_message_processed(channel_id, message_id, message_text, summary)
                    logger.info(f"✅ Message marked as processed: ID {result}")
                    return result
                except Exception as e:
                    logger.error(f"❌ PostgreSQL mark_message_processed failed: {e}")
                    raise
        
        # Используем PostgreSQL классы
        ChannelsDB = LoggedChannelsDB
        SettingsDB = LoggedSettingsDB
        ProcessedMessagesDB = LoggedProcessedMessagesDB
        
        def create_connection():
            logger.debug("🔵 PostgreSQL: create_connection()")
            try:
                if not supabase_db.initialized:
                    logger.info("🔧 Initializing Supabase connection...")
                    if not supabase_db.initialize():
                        raise Exception("Supabase initialization failed")
                
                connection = supabase_db.get_connection()
                logger.info("✅ PostgreSQL connection established")
                return connection
            except Exception as e:
                logger.error(f"❌ PostgreSQL connection failed: {e}")
                raise
        
        def init_database():
            logger.debug("🔵 PostgreSQL: init_database()")
            try:
                logger.info("🚀 Initializing PostgreSQL database...")
                result = init_supabase_database()
                logger.info("✅ PostgreSQL database initialized")
                return result
            except Exception as e:
                logger.error(f"❌ PostgreSQL init failed: {e}")
                raise
        
        def test_db():
            logger.debug("🔵 PostgreSQL: test_db()")
            try:
                result = test_supabase_db()
                if result:
                    logger.info("✅ PostgreSQL test passed")
                else:
                    logger.warning("⚠️ PostgreSQL test failed")
                return result
            except Exception as e:
                logger.error(f"❌ PostgreSQL test failed: {e}")
                raise
                
        logger.info("✅ Using PostgreSQL (Supabase) database")
        
    except Exception as e:
        logger.error(f"❌ Failed to set up PostgreSQL: {e}")
        logger.error("🔄 PostgreSQL configured but not working - check Supabase setup")
        has_postgres_config = False

if not has_postgres_config:
    # Fallback к SQLite
    logger.warning("⚠️ PostgreSQL not available - using SQLite fallback")
    logger.warning("🚨 THIS IS NOT RECOMMENDED FOR PRODUCTION!")
    
    try:
        from .database import (
            init_database as _sqlite_init,
            test_db as _sqlite_test,
            ChannelsDB as _SQLiteChannelsDB,
            SettingsDB as _SQLiteSettingsDB,
            ProcessedMessagesDB as _SQLiteProcessedMessagesDB,
            create_connection as _sqlite_connection,
        )
    except ImportError:
        from database import (
            init_database as _sqlite_init,
            test_db as _sqlite_test,
            ChannelsDB as _SQLiteChannelsDB,
            SettingsDB as _SQLiteSettingsDB,
            ProcessedMessagesDB as _SQLiteProcessedMessagesDB,
            create_connection as _sqlite_connection,
        )
    
    # Wrapper классы с предупреждениями
    class FallbackChannelsDB:
        @staticmethod
        def add_channel(username: str, display_name: str = None, priority: int = 0) -> int:
            logger.warning(f"⚠️ SQLite FALLBACK: add_channel({username})")
            logger.warning("💡 Add PostgreSQL configuration for production use")
            return _SQLiteChannelsDB.add_channel(username, display_name, priority)
            
        @staticmethod
        def get_active_channels():
            logger.warning("⚠️ SQLite FALLBACK: get_active_channels()")
            return _SQLiteChannelsDB.get_active_channels()
            
        @staticmethod
        def update_last_message_id(channel_id: int, message_id: int):
            logger.warning(f"⚠️ SQLite FALLBACK: update_last_message_id({channel_id})")
            return _SQLiteChannelsDB.update_last_message_id(channel_id, message_id)
    
    class FallbackSettingsDB:
        @staticmethod
        def get_setting(key: str, default: str = None):
            logger.debug(f"⚠️ SQLite FALLBACK: get_setting({key})")
            return _SQLiteSettingsDB.get_setting(key, default)
            
        @staticmethod
        def set_setting(key: str, value: str, description: str = None):
            logger.warning(f"⚠️ SQLite FALLBACK: set_setting({key})")
            return _SQLiteSettingsDB.set_setting(key, value, description)
    
    class FallbackProcessedMessagesDB:
        @staticmethod
        def is_message_processed(channel_id: int, message_id: int) -> bool:
            return _SQLiteProcessedMessagesDB.is_message_processed(channel_id, message_id)
            
        @staticmethod
        def mark_message_processed(channel_id: int, message_id: int, message_text: str = None, summary: str = None) -> int:
            return _SQLiteProcessedMessagesDB.mark_message_processed(channel_id, message_id, message_text, summary)
    
    ChannelsDB = FallbackChannelsDB
    SettingsDB = FallbackSettingsDB  
    ProcessedMessagesDB = FallbackProcessedMessagesDB
    create_connection = _sqlite_connection
    init_database = _sqlite_init
    test_db = _sqlite_test
    
    logger.info("✅ Using SQLite fallback database")

def get_database_info() -> Dict[str, Any]:
    """Возвращает информацию о текущей базе данных"""
    if has_postgres_config:
        return {
            'type': 'PostgreSQL (Supabase)',
            'url': SUPABASE_URL,
            'database_url': DATABASE_URL[:50] + "..." if DATABASE_URL else None,
            'persistent': True,
            'railway_compatible': True,
            'fallback_available': True,
            'production_ready': True
        }
    else:
        from .config import DATABASE_PATH
        return {
            'type': 'SQLite (Fallback)',
            'path': DATABASE_PATH,
            'persistent': '/data/' in DATABASE_PATH if DATABASE_PATH else False,
            'railway_compatible': False,
            'fallback_available': False,
            'production_ready': False
        }

# Экспортируем все необходимые функции и классы
__all__ = [
    'init_database',
    'test_db', 
    'ChannelsDB',
    'SettingsDB',
    'ProcessedMessagesDB',
    'create_connection',
    'get_database_info'
]

if __name__ == "__main__":
    logger.info("🧪 Testing DB Adapter...")
    
    db_info = get_database_info()
    logger.info(f"🗄️ Database info: {db_info}")
    
    try:
        init_database()
        logger.info("✅ Database initialized!")
        
        if test_db():
            logger.info("✅ Database test passed!")
        else:
            logger.error("❌ Database test failed!")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
