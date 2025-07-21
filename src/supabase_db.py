#!/usr/bin/env python3
"""
Модуль для работы с базой данных Supabase (PostgreSQL)
Замена SQLite на более надежную PostgreSQL через Supabase
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor

# Настройка логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/supabase_db.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Конфигурация Supabase
try:
    from .config import SUPABASE_URL, SUPABASE_KEY, DATABASE_URL
except ImportError:
    from config import SUPABASE_URL, SUPABASE_KEY, DATABASE_URL

class SupabaseDB:
    """Класс для работы с Supabase PostgreSQL"""
    
    def __init__(self):
        self.supabase: Client = None
        self.pg_connection = None
        self.initialized = False
    
    def initialize(self):
        """Инициализация подключения к Supabase"""
        try:
            logger.info("🔗 Инициализация подключения к Supabase...")
            
            # Проверка конфигурации
            if not SUPABASE_URL:
                raise ValueError("❌ SUPABASE_URL не настроен")
            if not SUPABASE_KEY:
                raise ValueError("❌ SUPABASE_ANON_KEY не настроен")
            if not DATABASE_URL:
                raise ValueError("❌ DATABASE_URL не настроен")
            
            logger.info(f"🔍 Supabase URL: {SUPABASE_URL}")
            logger.info(f"🔑 API Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "❌ API Key не найден")
            
            # Подключение через Supabase client
            if SUPABASE_URL and SUPABASE_KEY:
                try:
                    # Создаем client с минимальными параметрами
                    self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    logger.info("✅ Supabase client инициализирован")
                except TypeError as client_error:
                    if "proxy" in str(client_error):
                        logger.warning(f"⚠️ Версия supabase-py не поддерживает proxy: {client_error}")
                        logger.info("💡 Обновите supabase до версии 2.3.4 или используем прямое подключение")
                    else:
                        logger.warning(f"⚠️ Ошибка создания Supabase client: {client_error}")
                    logger.info("💡 Продолжаем с прямым подключением к PostgreSQL")
                except Exception as client_error:
                    logger.warning(f"⚠️ Не удалось создать Supabase client: {client_error}")
                    logger.info("💡 Продолжаем с прямым подключением к PostgreSQL")
            
            # Прямое подключение к PostgreSQL для некоторых операций
            if DATABASE_URL:
                try:
                    self.pg_connection = psycopg2.connect(
                        DATABASE_URL,
                        cursor_factory=RealDictCursor,
                        connect_timeout=10,  # 10 секунд таймаут
                        application_name="edu_digest_bot"
                    )
                    self.pg_connection.autocommit = True
                    logger.info("✅ PostgreSQL подключение установлено")
                except psycopg2.OperationalError as pg_error:
                    logger.error(f"❌ Не удалось подключиться к PostgreSQL: {pg_error}")
                    if "Network is unreachable" in str(pg_error):
                        logger.error("🌐 Сетевая проблема - возможно Railway не может достучаться до Supabase")
                        logger.error("💡 Проверьте настройки Supabase и DATABASE_URL")
                    raise
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Supabase: {e}")
            if "SUPABASE_URL" in str(e) or "SUPABASE_ANON_KEY" in str(e) or "DATABASE_URL" in str(e):
                logger.error("💡 Проверьте настройки в переменных окружения:")
                logger.error("   - SUPABASE_URL (Project URL)")
                logger.error("   - SUPABASE_ANON_KEY (anon public key)")  
                logger.error("   - DATABASE_URL (PostgreSQL connection string)")
            return False
    
    def get_connection(self):
        """Получение подключения к PostgreSQL"""
        if not self.pg_connection:
            if DATABASE_URL:
                self.pg_connection = psycopg2.connect(
                    DATABASE_URL,
                    cursor_factory=RealDictCursor
                )
                self.pg_connection.autocommit = True
        return self.pg_connection

# Глобальный экземпляр
supabase_db = SupabaseDB()

def init_supabase_database():
    """Инициализация базы данных Supabase с созданием всех таблиц"""
    try:
        logger.info("🚀 Инициализация базы данных Supabase...")
        
        if not supabase_db.initialize():
            raise Exception("Не удалось инициализировать Supabase")
        
        # Создаем таблицы через SQL
        conn = supabase_db.get_connection()
        cursor = conn.cursor()
        
        logger.info("📊 Создание таблиц...")
        
        # Таблица отслеживаемых каналов
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
        
        # Таблица обработанных сообщений
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
        
        # Таблица настроек системы
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
        
        # Таблица логов запусков
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
        
        # Вставка настроек по умолчанию
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
        
        logger.info("✅ База данных Supabase успешно инициализирована")
        
        # Проверка созданных таблиц
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        logger.info(f"📋 Созданные таблицы: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных Supabase: {e}")
        raise

def test_supabase_db() -> bool:
    """Тестирование подключения к Supabase"""
    try:
        if not supabase_db.initialized:
            supabase_db.initialize()
        
        conn = supabase_db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()['count']
        return table_count >= 4  # Ожидаем минимум 4 таблицы
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования Supabase DB: {e}")
        return False

# Функции для работы с каналами
class SupabaseChannelsDB:
    @staticmethod
    def add_channel(username: str, display_name: str = None, priority: int = 0) -> int:
        """Добавление нового канала"""
        try:
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO channels (username, display_name, priority)
                VALUES (%s, %s, %s)
                RETURNING id
            ''', (username, display_name or username, priority))
            
            channel_id = cursor.fetchone()['id']
            logger.info(f"✅ Добавлен канал: {username} (ID: {channel_id})")
            return channel_id
            
        except psycopg2.IntegrityError as e:
            if "duplicate key" in str(e):
                logger.warning(f"⚠️ Канал {username} уже существует")
                raise ValueError(f"Канал {username} уже существует")
            else:
                logger.error(f"❌ Ошибка добавления канала {username}: {e}")
                raise
        except Exception as e:
            logger.error(f"❌ Ошибка добавления канала {username}: {e}")
            raise
    
    @staticmethod
    def get_active_channels() -> List[Dict]:
        """Получение списка активных каналов по приоритету"""
        try:
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM channels 
                WHERE is_active = true 
                ORDER BY priority DESC, created_at ASC
            ''')
            
            channels = [dict(row) for row in cursor.fetchall()]
            return channels
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения каналов: {e}")
            return []
    
    @staticmethod
    def update_last_message_id(channel_id: int, message_id: int):
        """Обновление ID последнего обработанного сообщения"""
        try:
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE channels 
                SET last_message_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (message_id, channel_id))
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления last_message_id: {e}")
            raise

# Функции для работы с настройками
class SupabaseSettingsDB:
    @staticmethod
    def get_setting(key: str, default: str = None) -> Optional[str]:
        """Получение значения настройки"""
        try:
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM settings WHERE key = %s', (key,))
            result = cursor.fetchone()
            return result['value'] if result else default
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения настройки {key}: {e}")
            return default
    
    @staticmethod
    def set_setting(key: str, value: str, description: str = None):
        """Установка значения настройки"""
        try:
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO settings (key, value, description, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    description = COALESCE(EXCLUDED.description, settings.description),
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, value, description))
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки настройки {key}: {e}")
            raise

# Функции для работы с обработанными сообщениями
class SupabaseProcessedMessagesDB:
    @staticmethod
    def is_message_processed(channel_id: int, message_id: int) -> bool:
        """Проверка, было ли сообщение уже обработано"""
        try:
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 1 FROM processed_messages 
                WHERE channel_id = %s AND message_id = %s
            ''', (channel_id, message_id))
            
            return cursor.fetchone() is not None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки сообщения: {e}")
            return False
    
    @staticmethod
    def mark_message_processed(channel_id: int, message_id: int, 
                             message_text: str = None, summary: str = None) -> int:
        """Отметка сообщения как обработанного"""
        try:
            conn = supabase_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO processed_messages 
                (channel_id, message_id, message_text, summary)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (channel_id, message_id) DO NOTHING
                RETURNING id
            ''', (channel_id, message_id, message_text, summary))
            
            result = cursor.fetchone()
            return result['id'] if result else 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка отметки сообщения: {e}")
            return 0

if __name__ == "__main__":
    # Тестирование при прямом запуске
    try:
        init_supabase_database()
        print("✅ База данных Supabase инициализирована успешно!")
        
        if test_supabase_db():
            print("✅ Тестирование Supabase прошло успешно!")
        else:
            print("❌ Ошибка при тестировании Supabase!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")