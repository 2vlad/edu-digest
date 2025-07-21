import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
try:
    from .config import DATABASE_PATH
except ImportError:
    from config import DATABASE_PATH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_connection() -> sqlite3.Connection:
    """Создание подключения к базе данных"""
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise

def init_database():
    """Инициализация базы данных с созданием всех таблиц"""
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Таблица отслеживаемых каналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT,
                priority INTEGER DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
                is_active BOOLEAN DEFAULT 1,
                last_message_id INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица обработанных сообщений (для избежания дублей)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                message_text TEXT,
                summary TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published BOOLEAN DEFAULT 0,
                FOREIGN KEY (channel_id) REFERENCES channels (id),
                UNIQUE(channel_id, message_id)
            )
        ''')
        
        # Настройки системы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица логов запусков (для мониторинга)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        cursor.executemany('''
            INSERT OR IGNORE INTO settings (key, value, description) 
            VALUES (?, ?, ?)
        ''', default_settings)
        
        conn.commit()
        logger.info("База данных успешно инициализирована")
        logger.info(f"Файл базы данных: {DATABASE_PATH}")
        
        # Проверка созданных таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Созданные таблицы: {', '.join(tables)}")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def test_db() -> bool:
    """Тестирование подключения к базе данных"""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        conn.close()
        return table_count >= 4  # Ожидаем минимум 4 таблицы
    except Exception as e:
        logger.error(f"Ошибка тестирования БД: {e}")
        return False

# Функции для работы с каналами
class ChannelsDB:
    @staticmethod
    def add_channel(username: str, display_name: str = None, priority: int = 0) -> int:
        """Добавление нового канала"""
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO channels (username, display_name, priority)
                VALUES (?, ?, ?)
            ''', (username, display_name or username, priority))
            conn.commit()
            channel_id = cursor.lastrowid
            logger.info(f"Добавлен канал: {username} (ID: {channel_id})")
            return channel_id
        except sqlite3.IntegrityError:
            logger.warning(f"Канал {username} уже существует")
            raise
        except Exception as e:
            logger.error(f"Ошибка добавления канала {username}: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def get_active_channels() -> List[Dict]:
        """Получение списка активных каналов по приоритету"""
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM channels 
                WHERE is_active = 1 
                ORDER BY priority DESC, created_at ASC
            ''')
            channels = [dict(row) for row in cursor.fetchall()]
            return channels
        finally:
            conn.close()
    
    @staticmethod
    def update_last_message_id(channel_id: int, message_id: int):
        """Обновление ID последнего обработанного сообщения"""
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE channels 
                SET last_message_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (message_id, channel_id))
            conn.commit()
        finally:
            conn.close()

# Функции для работы с настройками
class SettingsDB:
    @staticmethod
    def get_setting(key: str, default: str = None) -> Optional[str]:
        """Получение значения настройки"""
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else default
        finally:
            conn.close()
    
    @staticmethod
    def set_setting(key: str, value: str, description: str = None):
        """Установка значения настройки"""
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value, description))
            conn.commit()
        finally:
            conn.close()

# Функции для работы с обработанными сообщениями
class ProcessedMessagesDB:
    @staticmethod
    def is_message_processed(channel_id: int, message_id: int) -> bool:
        """Проверка, было ли сообщение уже обработано"""
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT 1 FROM processed_messages 
                WHERE channel_id = ? AND message_id = ?
            ''', (channel_id, message_id))
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    @staticmethod
    def mark_message_processed(channel_id: int, message_id: int, 
                             message_text: str = None, summary: str = None) -> int:
        """Отметка сообщения как обработанного"""
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO processed_messages 
                (channel_id, message_id, message_text, summary)
                VALUES (?, ?, ?, ?)
            ''', (channel_id, message_id, message_text, summary))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

if __name__ == "__main__":
    # Инициализация базы данных при прямом запуске
    init_database()
    print("✅ База данных инициализирована успешно!")
    
    # Тест подключения
    if test_db():
        print("✅ Тестирование базы данных прошло успешно!")
    else:
        print("❌ Ошибка при тестировании базы данных!")