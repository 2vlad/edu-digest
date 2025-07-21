#!/usr/bin/env python3
"""
Адаптер базы данных - СТРОГО ТОЛЬКО SUPABASE PostgreSQL
Никаких fallback на SQLite!
"""

import logging
import os
from typing import List, Dict, Optional, Any

# Настройка детального логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,  # Самый детальный уровень
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_adapter.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

logger.info("🚀 Initializing DB Adapter - SUPABASE ONLY MODE")

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

if not DATABASE_URL or not SUPABASE_URL:
    logger.error("❌ CRITICAL: Supabase configuration missing!")
    logger.error("💡 Required environment variables:")
    logger.error("   - DATABASE_URL (PostgreSQL connection string)")
    logger.error("   - SUPABASE_URL (Project URL)")
    logger.error("   - SUPABASE_ANON_KEY (Anonymous key)")
    raise ValueError("Supabase configuration missing - cannot proceed with SUPABASE ONLY mode")

# Импортируем Supabase модули
logger.info("📦 Importing Supabase modules...")
try:
    from .supabase_db import (
        init_supabase_database,
        test_supabase_db,
        SupabaseChannelsDB,
        SupabaseSettingsDB,
        SupabaseProcessedMessagesDB,
        supabase_db
    )
    logger.info("✅ Supabase modules imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import Supabase modules: {e}")
    logger.info("🔄 Trying fallback import...")
    try:
        from supabase_db import (
            init_supabase_database,
            test_supabase_db,
            SupabaseChannelsDB,
            SupabaseSettingsDB,
            SupabaseProcessedMessagesDB,
            supabase_db
        )
        logger.info("✅ Supabase modules imported via fallback")
    except ImportError as fallback_error:
        logger.error(f"❌ CRITICAL: Cannot import Supabase modules: {fallback_error}")
        raise ImportError(f"Cannot import Supabase modules: {fallback_error}")

# Создаем строго Supabase-only классы с детальным логированием
class SupabaseOnlyChannelsDB:
    @staticmethod
    def add_channel(username: str, display_name: str = None, priority: int = 0) -> int:
        logger.debug(f"🔵 ChannelsDB.add_channel called: username={username}, display_name={display_name}, priority={priority}")
        try:
            result = SupabaseChannelsDB.add_channel(username, display_name, priority)
            logger.info(f"✅ Channel added successfully: {username} -> ID {result}")
            return result
        except Exception as e:
            logger.error(f"❌ FAILED to add channel {username}: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise e  # Re-raise - NO FALLBACK!
            
    @staticmethod
    def get_active_channels():
        logger.debug("🔵 ChannelsDB.get_active_channels called")
        try:
            result = SupabaseChannelsDB.get_active_channels()
            logger.info(f"✅ Active channels retrieved: {len(result)} channels")
            for channel in result:
                logger.debug(f"   📺 {channel.get('display_name', 'Unknown')} ({channel.get('username', 'Unknown')})")
            return result
        except Exception as e:
            logger.error(f"❌ FAILED to get active channels: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise e  # Re-raise - NO FALLBACK!
            
    @staticmethod
    def update_last_message_id(channel_id: int, message_id: int):
        logger.debug(f"🔵 ChannelsDB.update_last_message_id called: channel_id={channel_id}, message_id={message_id}")
        try:
            result = SupabaseChannelsDB.update_last_message_id(channel_id, message_id)
            logger.info(f"✅ Last message ID updated for channel {channel_id}")
            return result
        except Exception as e:
            logger.error(f"❌ FAILED to update last message ID for channel {channel_id}: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise e  # Re-raise - NO FALLBACK!

class SupabaseOnlySettingsDB:
    @staticmethod
    def get_setting(key: str, default: str = None):
        logger.debug(f"🔵 SettingsDB.get_setting called: key={key}, default={default}")
        try:
            result = SupabaseSettingsDB.get_setting(key, default)
            logger.info(f"✅ Setting retrieved: {key} = {result}")
            return result
        except Exception as e:
            logger.error(f"❌ FAILED to get setting {key}: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise e  # Re-raise - NO FALLBACK!
            
    @staticmethod
    def set_setting(key: str, value: str, description: str = None):
        logger.debug(f"🔵 SettingsDB.set_setting called: key={key}, value={value}, description={description}")
        try:
            result = SupabaseSettingsDB.set_setting(key, value, description)
            logger.info(f"✅ Setting updated: {key} = {value}")
            return result
        except Exception as e:
            logger.error(f"❌ FAILED to set setting {key}: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise e  # Re-raise - NO FALLBACK!

class SupabaseOnlyProcessedMessagesDB:
    @staticmethod
    def is_message_processed(channel_id: int, message_id: int) -> bool:
        logger.debug(f"🔵 ProcessedMessagesDB.is_message_processed called: channel_id={channel_id}, message_id={message_id}")
        try:
            result = SupabaseProcessedMessagesDB.is_message_processed(channel_id, message_id)
            logger.debug(f"✅ Message processed check: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ FAILED to check if message processed: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise e  # Re-raise - NO FALLBACK!
            
    @staticmethod
    def mark_message_processed(channel_id: int, message_id: int, message_text: str = None, summary: str = None) -> int:
        logger.debug(f"🔵 ProcessedMessagesDB.mark_message_processed called: channel_id={channel_id}, message_id={message_id}")
        try:
            result = SupabaseProcessedMessagesDB.mark_message_processed(channel_id, message_id, message_text, summary)
            logger.info(f"✅ Message marked as processed: ID {result}")
            return result
        except Exception as e:
            logger.error(f"❌ FAILED to mark message as processed: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise e  # Re-raise - NO FALLBACK!

# Экспортируем Supabase-only классы
ChannelsDB = SupabaseOnlyChannelsDB
SettingsDB = SupabaseOnlySettingsDB
ProcessedMessagesDB = SupabaseOnlyProcessedMessagesDB

def create_connection():
    """Получение подключения СТРОГО только к Supabase"""
    logger.debug("🔵 create_connection called")
    try:
        if not supabase_db.initialized:
            logger.info("🔧 Supabase not initialized, initializing...")
            if not supabase_db.initialize():
                raise Exception("Supabase initialization failed")
        
        connection = supabase_db.get_connection()
        logger.info("✅ Supabase connection established")
        return connection
    except Exception as e:
        logger.error(f"❌ FAILED to create Supabase connection: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        raise e  # Re-raise - NO FALLBACK!

def init_database():
    """Инициализация БД СТРОГО только Supabase"""
    logger.debug("🔵 init_database called")
    try:
        logger.info("🚀 Initializing Supabase database...")
        result = init_supabase_database()
        logger.info("✅ Supabase database initialized successfully")
        return result
    except Exception as e:
        logger.error(f"❌ FAILED to initialize Supabase database: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        raise e  # Re-raise - NO FALLBACK!

def test_db():
    """Тестирование БД СТРОГО только Supabase"""
    logger.debug("🔵 test_db called")
    try:
        logger.info("🧪 Testing Supabase database...")
        result = test_supabase_db()
        if result:
            logger.info("✅ Supabase database test passed")
        else:
            logger.warning("⚠️ Supabase database test failed")
        return result
    except Exception as e:
        logger.error(f"❌ FAILED to test Supabase database: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        raise e  # Re-raise - NO FALLBACK!

# Экспортируем все необходимые функции и классы
__all__ = [
    'init_database',
    'test_db', 
    'ChannelsDB',
    'SettingsDB',
    'ProcessedMessagesDB',
    'create_connection',
]

def get_database_info() -> Dict[str, Any]:
    """Возвращает информацию о текущей базе данных"""
    logger.debug("🔵 get_database_info called")
    return {
        'type': 'PostgreSQL (Supabase ONLY)',
        'url': SUPABASE_URL,
        'database_url': DATABASE_URL[:50] + "..." if DATABASE_URL else None,
        'persistent': True,
        'railway_compatible': True,
        'fallback_available': False,  # Строго NO FALLBACK!
        'supabase_only': True
    }

if __name__ == "__main__":
    # Тестирование адаптера
    logger.info("🧪 Testing DB Adapter in SUPABASE ONLY mode...")
    
    db_info = get_database_info()
    logger.info(f"🗄️ Database info: {db_info}")
    print(f"🗄️ Database info: {db_info}")
    
    try:
        logger.info("🔧 Initializing database...")
        init_database()
        logger.info("✅ Database initialized successfully!")
        print("✅ Database initialized successfully!")
        
        logger.info("🧪 Testing database...")
        if test_db():
            logger.info("✅ Database test passed!")
            print("✅ Database test passed!")
        else:
            logger.error("❌ Database test failed!")
            print("❌ Database test failed!")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"❌ Error: {e}")
        import traceback
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")