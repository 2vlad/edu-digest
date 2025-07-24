#!/usr/bin/env python3
"""
Модуль для работы с базой данных Supabase (PostgreSQL)
ТОЛЬКО SUPABASE - БЕЗ SQLite FALLBACK
Гибридный подход: REST API + PostgreSQL
"""

import os
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor

# Настройка логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database.log'),
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
    """Класс для работы с Supabase через REST API и PostgreSQL"""
    
    def __init__(self):
        self.supabase: Client = None
        self.pg_connection = None
        self.initialized = False
        self.rest_api_url = None
        self.headers = None
    
    def initialize(self):
        """Инициализация подключения к Supabase"""
        try:
            logger.info("🔗 Инициализация подключения к Supabase...")
            
            # Проверка обязательных переменных
            if not SUPABASE_URL:
                raise ValueError("❌ SUPABASE_URL не настроен в переменных окружения")
            if not SUPABASE_KEY:
                raise ValueError("❌ SUPABASE_ANON_KEY не настроен в переменных окружения")
            
            logger.info(f"🔍 Supabase URL: {SUPABASE_URL}")
            logger.info(f"🔑 API Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "❌ API Key не найден")
            
            # Настройка REST API
            self.rest_api_url = f"{SUPABASE_URL}/rest/v1"
            self.headers = {
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
            
            # Проверяем доступность REST API
            try:
                response = requests.get(f"{self.rest_api_url}/", headers=self.headers, timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Supabase REST API доступен")
                else:
                    logger.warning(f"⚠️ REST API вернул код: {response.status_code}")
            except Exception as api_error:
                logger.warning(f"⚠️ REST API недоступен: {api_error}")
            
            # Создаем Supabase client (опционально)
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("✅ Supabase client инициализирован")
            except Exception as supabase_error:
                logger.warning(f"⚠️ Supabase client не инициализирован: {supabase_error}")
                logger.info("📝 Будем использовать только REST API")
                self.supabase = None
            
            # Пытаемся настроить PostgreSQL подключение (если доступно)
            if DATABASE_URL:
                try:
                    self.pg_connection = psycopg2.connect(
                        DATABASE_URL,
                        cursor_factory=RealDictCursor,
                        connect_timeout=5,
                        application_name="edu_digest_bot"
                    )
                    self.pg_connection.autocommit = True
                    logger.info("✅ PostgreSQL подключение установлено")
                except Exception as pg_error:
                    logger.warning(f"⚠️ PostgreSQL подключение неудачно: {pg_error}")
                    logger.info("📝 Будем использовать только REST API")
                    self.pg_connection = None
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Supabase: {e}")
            logger.error("💡 Проверьте переменные окружения:")
            logger.error("   - SUPABASE_URL (Project URL)")
            logger.error("   - SUPABASE_ANON_KEY (anon public key)")  
            logger.error("   - DATABASE_URL (PostgreSQL connection string)")
            raise
    
    def execute_rest_query(self, table: str, method: str = 'GET', data: Dict = None, filters: Dict = None):
        """Выполнение запроса через REST API"""
        if not self.initialized:
            self.initialize()
        
        try:
            url = f"{self.rest_api_url}/{table}"
            
            # Добавляем фильтры
            if filters:
                params = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        params.append(f"{key}=eq.{value}")
                    else:
                        params.append(f"{key}=eq.{value}")
                if params:
                    url += "?" + "&".join(params)
            
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code in [200, 201, 204]:
                try:
                    return response.json() if response.content else []
                except:
                    return []
            elif response.status_code == 409:
                # Конфликт - обычно означает нарушение уникального ограничения
                error_detail = ""
                try:
                    error_data = response.json()
                    if 'details' in error_data:
                        error_detail = error_data['details']
                    elif 'message' in error_data:
                        error_detail = error_data['message']
                except:
                    pass
                
                if 'duplicate' in error_detail.lower() or 'unique' in error_detail.lower():
                    raise ValueError("Такой элемент уже существует")
                else:
                    raise ValueError(f"Конфликт данных: {error_detail}")
            else:
                logger.error(f"❌ REST API error {response.status_code}: {response.text}")
                raise Exception(f"REST API error: {response.status_code}")
                
        except ValueError:
            # Пробрасываем ValueError (это наши ошибки валидации)
            raise
        except Exception as e:
            logger.error(f"❌ REST API запрос неудачен: {e}")
            raise
    
    def get_connection(self):
        """Получение подключения к PostgreSQL (если доступно)"""
        if not self.initialized:
            self.initialize()
        
        if self.pg_connection and not self.pg_connection.closed:
            return self.pg_connection
        
        # Если PostgreSQL недоступен, возвращаем None
        # В этом случае будем использовать REST API
        return None

# Глобальный экземпляр
supabase_db = SupabaseDB()

def init_database():
    """Инициализация базы данных Supabase с созданием всех таблиц"""
    try:
        logger.info("🚀 Инициализация базы данных Supabase...")
        
        if not supabase_db.initialize():
            raise Exception("Не удалось инициализировать Supabase")
        
        # Создаем таблицы через SQL
        conn = supabase_db.get_connection()
        if conn is None:
            logger.warning("⚠️ PostgreSQL недоступен, используем REST API для инициализации")
            # Таблицы должны быть созданы в Supabase Dashboard или через SQL редактор
            # Проверяем доступность через REST API
            try:
                result = supabase_db.execute_rest_query('channels', 'GET')
                logger.info("✅ Таблица channels доступна через REST API")
                return True
            except Exception as api_error:
                logger.error(f"❌ REST API тест неудачен: {api_error}")
                raise Exception("База данных недоступна через REST API")
        
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
        
        # Настройки системы
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
                INSERT INTO settings (key, value, description, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO NOTHING
            ''', (key, value, description))
        
        logger.info("✅ База данных Supabase успешно инициализирована")
        
        # Проверка созданных таблиц
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        logger.info(f"✅ Созданные таблицы: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных Supabase: {e}")
        raise

def test_db() -> bool:
    """Тестирование подключения к Supabase"""
    try:
        if not supabase_db.initialized:
            supabase_db.initialize()
        
        conn = supabase_db.get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Простой тест
            cursor.execute('SELECT 1 as test')
            result = cursor.fetchone()
            
            if result and result['test'] == 1:
                logger.info("✅ Подключение к Supabase через PostgreSQL работает")
                return True
            else:
                logger.error("❌ Тест подключения к Supabase провалился")
                return False
        else:
            # Тестируем REST API
            logger.info("🔍 Тестируем подключение через REST API...")
            try:
                result = supabase_db.execute_rest_query('channels', 'GET')
                logger.info("✅ Подключение к Supabase через REST API работает")
                return True
            except Exception as api_error:
                logger.error(f"❌ REST API тест неудачен: {api_error}")
                return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования Supabase DB: {e}")
        return False

def create_connection():
    """Создание подключения к базе данных"""
    return supabase_db.get_connection()

# Функции для работы с каналами
class ChannelsDB:
    @staticmethod
    def add_channel(username: str, display_name: str = None, priority: int = 0) -> int:
        """Добавление нового канала"""
        try:
            # Сначала пытаемся PostgreSQL
            conn = supabase_db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO channels (username, display_name, priority, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id
                ''', (username, display_name or username, priority))
                
                result = cursor.fetchone()
                channel_id = result['id']
                logger.info(f"✅ Добавлен канал через PostgreSQL: {username} (ID: {channel_id})")
                return channel_id
            else:
                # Используем REST API
                logger.info("📡 Используем REST API для добавления канала")
                data = {
                    'username': username,
                    'display_name': display_name or username,
                    'priority': priority,
                    'updated_at': datetime.now().isoformat()
                }
                
                result = supabase_db.execute_rest_query('channels', 'POST', data)
                if result and len(result) > 0:
                    channel_id = result[0]['id']
                    logger.info(f"✅ Добавлен канал через REST API: {username} (ID: {channel_id})")
                    return channel_id
                else:
                    raise Exception("Не удалось добавить канал через REST API")
            
        except psycopg2.IntegrityError:
            logger.warning(f"⚠️ Канал {username} уже существует")
            raise ValueError(f"Канал {username} уже существует")
        except ValueError as ve:
            # Если это уже ValueError (от REST API или другой валидации), просто пробрасываем
            if "уже существует" in str(ve) or "already exists" in str(ve).lower():
                logger.warning(f"⚠️ Канал {username} уже существует")
                raise ValueError(f"Канал {username} уже существует")
            else:
                raise ve
        except Exception as e:
            logger.error(f"❌ Ошибка добавления канала {username}: {e}")
            
            # Если PostgreSQL не сработал, пробуем REST API как fallback
            if 'connection' in str(e).lower() or 'gssapi' in str(e).lower():
                try:
                    logger.info("📡 Fallback на REST API для добавления канала")
                    data = {
                        'username': username,
                        'display_name': display_name or username,
                        'priority': priority,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    result = supabase_db.execute_rest_query('channels', 'POST', data)
                    if result and len(result) > 0:
                        channel_id = result[0]['id']
                        logger.info(f"✅ Добавлен канал через REST API fallback: {username} (ID: {channel_id})")
                        return channel_id
                    else:
                        raise Exception("Не удалось добавить канал через REST API fallback")
                except ValueError as ve:
                    # Обрабатываем ошибки валидации от REST API
                    if "уже существует" in str(ve) or "already exists" in str(ve).lower():
                        logger.warning(f"⚠️ Канал {username} уже существует (REST API)")
                        raise ValueError(f"Канал {username} уже существует")
                    else:
                        raise ve
                except Exception as api_error:
                    logger.error(f"❌ REST API fallback тоже не сработал: {api_error}")
                    raise
            else:
                raise
    
    @staticmethod
    def get_active_channels() -> List[Dict]:
        """Получение списка активных каналов по приоритету"""
        try:
            # Сначала пытаемся PostgreSQL
            conn = supabase_db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM channels 
                    WHERE is_active = true 
                    ORDER BY priority DESC, created_at ASC
                ''')
                
                channels = [dict(row) for row in cursor.fetchall()]
                logger.info(f"✅ Получено {len(channels)} каналов через PostgreSQL")
                return channels
            else:
                # Используем REST API
                logger.info("📡 Используем REST API для получения каналов")
                result = supabase_db.execute_rest_query('channels', 'GET', filters={'is_active': 'true'})
                
                # Сортируем по приоритету
                if result:
                    result.sort(key=lambda x: (-x.get('priority', 0), x.get('created_at', '')))
                
                logger.info(f"✅ Получено {len(result)} каналов через REST API")
                return result
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения каналов: {e}")
            
            # Fallback на REST API
            if 'connection' in str(e).lower() or 'gssapi' in str(e).lower():
                try:
                    logger.info("📡 Fallback на REST API для получения каналов")
                    result = supabase_db.execute_rest_query('channels', 'GET', filters={'is_active': 'true'})
                    
                    # Сортируем по приоритету
                    if result:
                        result.sort(key=lambda x: (-x.get('priority', 0), x.get('created_at', '')))
                    
                    logger.info(f"✅ Получено {len(result)} каналов через REST API fallback")
                    return result
                except Exception as api_error:
                    logger.error(f"❌ REST API fallback тоже не сработал: {api_error}")
                    return []
            return []
    
    @staticmethod
    def delete_channel(channel_id: int) -> bool:
        """Удаление канала"""
        try:
            # Сначала пытаемся PostgreSQL
            conn = supabase_db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM channels WHERE id = %s', (channel_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Канал {channel_id} удален через PostgreSQL")
                    return True
                else:
                    logger.warning(f"⚠️ Канал {channel_id} не найден для удаления")
                    return False
            else:
                # Используем REST API
                logger.info("📡 Используем REST API для удаления канала")
                result = supabase_db.execute_rest_query('channels', 'DELETE', filters={'id': channel_id})
                logger.info(f"✅ Канал {channel_id} удален через REST API")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления канала {channel_id}: {e}")
            
            # Fallback на REST API
            if 'connection' in str(e).lower() or 'gssapi' in str(e).lower():
                try:
                    logger.info("📡 Fallback на REST API для удаления канала")
                    result = supabase_db.execute_rest_query('channels', 'DELETE', filters={'id': channel_id})
                    logger.info(f"✅ Канал {channel_id} удален через REST API fallback")
                    return True
                except Exception as api_error:
                    logger.error(f"❌ REST API fallback тоже не сработал: {api_error}")
                    raise
            else:
                raise
    
    @staticmethod
    def toggle_channel_status(channel_id: int) -> bool:
        """Переключение статуса канала (активен/неактивен)"""
        try:
            # Сначала получаем текущий статус
            current_channel = None
            
            # Пытаемся PostgreSQL
            conn = supabase_db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT is_active FROM channels WHERE id = %s', (channel_id,))
                result = cursor.fetchone()
                if result:
                    current_channel = result
                    new_status = not result['is_active']
                    
                    cursor.execute('''
                        UPDATE channels 
                        SET is_active = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (new_status, channel_id))
                    
                    if cursor.rowcount > 0:
                        logger.info(f"✅ Статус канала {channel_id} изменен на {new_status} через PostgreSQL")
                        return True
            else:
                # Используем REST API
                logger.info("📡 Используем REST API для изменения статуса канала")
                
                # Получаем текущий статус
                channels = supabase_db.execute_rest_query('channels', 'GET', filters={'id': channel_id})
                if channels and len(channels) > 0:
                    current_channel = channels[0]
                    new_status = not current_channel.get('is_active', True)
                    
                    update_data = {
                        'is_active': new_status,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    supabase_db.execute_rest_query('channels', 'PATCH', update_data, filters={'id': channel_id})
                    logger.info(f"✅ Статус канала {channel_id} изменен на {new_status} через REST API")
                    return True
                    
            if not current_channel:
                logger.warning(f"⚠️ Канал {channel_id} не найден")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка изменения статуса канала {channel_id}: {e}")
            
            # Fallback на REST API
            if 'connection' in str(e).lower() or 'gssapi' in str(e).lower():
                try:
                    logger.info("📡 Fallback на REST API для изменения статуса канала")
                    
                    # Получаем текущий статус
                    channels = supabase_db.execute_rest_query('channels', 'GET', filters={'id': channel_id})
                    if channels and len(channels) > 0:
                        current_channel = channels[0]
                        new_status = not current_channel.get('is_active', True)
                        
                        update_data = {
                            'is_active': new_status,
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        supabase_db.execute_rest_query('channels', 'PATCH', update_data, filters={'id': channel_id})
                        logger.info(f"✅ Статус канала {channel_id} изменен на {new_status} через REST API fallback")
                        return True
                    else:
                        logger.warning(f"⚠️ Канал {channel_id} не найден в fallback")
                        return False
                        
                except Exception as api_error:
                    logger.error(f"❌ REST API fallback тоже не сработал: {api_error}")
                    raise
            else:
                raise
    
    @staticmethod
    def update_last_message_id(channel_id: int, message_id: int):
        """Обновление ID последнего обработанного сообщения"""
        try:
            conn = supabase_db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE channels 
                    SET last_message_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (message_id, channel_id))
                
                logger.info(f"✅ Обновлен last_message_id для канала {channel_id}")
            else:
                # Используем REST API
                logger.info("📡 Используем REST API для обновления last_message_id")
                
                update_data = {
                    'last_message_id': message_id,
                    'updated_at': datetime.now().isoformat()
                }
                
                supabase_db.execute_rest_query('channels', 'PATCH', update_data, filters={'id': channel_id})
                logger.info(f"✅ Обновлен last_message_id для канала {channel_id} через REST API")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления last_message_id: {e}")
            
            # Fallback на REST API
            if 'connection' in str(e).lower() or 'gssapi' in str(e).lower():
                try:
                    logger.info("📡 Fallback на REST API для обновления last_message_id")
                    
                    update_data = {
                        'last_message_id': message_id,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    supabase_db.execute_rest_query('channels', 'PATCH', update_data, filters={'id': channel_id})
                    logger.info(f"✅ Обновлен last_message_id для канала {channel_id} через REST API fallback")
                    
                except Exception as api_error:
                    logger.error(f"❌ REST API fallback тоже не сработал: {api_error}")
                    raise
            else:
                raise

# Функции для работы с настройками
class SettingsDB:
    @staticmethod
    def get_setting(key: str, default: str = None) -> Optional[str]:
        """Получение значения настройки"""
        try:
            # Сначала пытаемся PostgreSQL
            conn = supabase_db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT value FROM settings WHERE key = %s', (key,))
                result = cursor.fetchone()
                value = result['value'] if result else default
                
                logger.debug(f"✅ Настройка {key} = {value} (PostgreSQL)")
                return value
            else:
                # Используем REST API
                logger.debug("📡 Используем REST API для получения настройки")
                result = supabase_db.execute_rest_query('settings', 'GET', filters={'key': key})
                
                if result and len(result) > 0:
                    value = result[0]['value']
                    logger.debug(f"✅ Настройка {key} = {value} (REST API)")
                    return value
                else:
                    logger.debug(f"✅ Настройка {key} = {default} (default)")
                    return default
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения настройки {key}: {e}")
            
            # Fallback на REST API
            if 'connection' in str(e).lower() or 'gssapi' in str(e).lower():
                try:
                    logger.debug("📡 Fallback на REST API для получения настройки")
                    result = supabase_db.execute_rest_query('settings', 'GET', filters={'key': key})
                    
                    if result and len(result) > 0:
                        value = result[0]['value']
                        logger.debug(f"✅ Настройка {key} = {value} (REST API fallback)")
                        return value
                    else:
                        return default
                except Exception as api_error:
                    logger.error(f"❌ REST API fallback тоже не сработал: {api_error}")
                    return default
            return default
    
    @staticmethod
    def set_setting(key: str, value: str, description: str = None):
        """Установка значения настройки"""
        try:
            # Сначала пытаемся PostgreSQL
            conn = supabase_db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO settings (key, value, description, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        description = COALESCE(EXCLUDED.description, settings.description),
                        updated_at = CURRENT_TIMESTAMP
                ''', (key, value, description))
                
                logger.info(f"✅ Настройка {key} установлена в {value} (PostgreSQL)")
            else:
                # Используем REST API - сначала пытаемся обновить, потом создать
                logger.info("📡 Используем REST API для установки настройки")
                
                # Проверяем, существует ли настройка
                existing = supabase_db.execute_rest_query('settings', 'GET', filters={'key': key})
                
                data = {
                    'key': key,
                    'value': value,
                    'description': description,
                    'updated_at': datetime.now().isoformat()
                }
                
                if existing and len(existing) > 0:
                    # Обновляем существующую
                    update_data = {
                        'value': value,
                        'updated_at': datetime.now().isoformat()
                    }
                    if description:
                        update_data['description'] = description
                    
                    supabase_db.execute_rest_query('settings', 'PATCH', update_data, filters={'key': key})
                    logger.info(f"✅ Настройка {key} обновлена в {value} (REST API)")
                else:
                    # Создаем новую
                    supabase_db.execute_rest_query('settings', 'POST', data)
                    logger.info(f"✅ Настройка {key} создана в {value} (REST API)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки настройки {key}: {e}")
            
            # Fallback на REST API
            if 'connection' in str(e).lower() or 'gssapi' in str(e).lower():
                try:
                    logger.info("📡 Fallback на REST API для установки настройки")
                    
                    # Проверяем, существует ли настройка
                    existing = supabase_db.execute_rest_query('settings', 'GET', filters={'key': key})
                    
                    data = {
                        'key': key,
                        'value': value,
                        'description': description,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    if existing and len(existing) > 0:
                        # Обновляем существующую
                        update_data = {
                            'value': value,
                            'updated_at': datetime.now().isoformat()
                        }
                        if description:
                            update_data['description'] = description
                        
                        supabase_db.execute_rest_query('settings', 'PATCH', update_data, filters={'key': key})
                        logger.info(f"✅ Настройка {key} обновлена в {value} (REST API fallback)")
                    else:
                        # Создаем новую
                        supabase_db.execute_rest_query('settings', 'POST', data)
                        logger.info(f"✅ Настройка {key} создана в {value} (REST API fallback)")
                        
                except Exception as api_error:
                    logger.error(f"❌ REST API fallback тоже не сработал: {api_error}")
                    raise
            else:
                raise

# Функции для работы с обработанными сообщениями
class ProcessedMessagesDB:
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
            
            result = cursor.fetchone()
            return result is not None
            
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
                (channel_id, message_id, message_text, summary, processed_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (channel_id, message_id) DO UPDATE SET
                    message_text = EXCLUDED.message_text,
                    summary = EXCLUDED.summary,
                    processed_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (channel_id, message_id, message_text, summary))
            
            result = cursor.fetchone()
            record_id = result['id']
            logger.info(f"✅ Сообщение {message_id} отмечено как обработанное (ID: {record_id})")
            return record_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка отметки сообщения: {e}")
            raise

def get_database_info() -> Dict[str, Any]:
    """Возвращает информацию о базе данных"""
    return {
        'type': 'PostgreSQL (Supabase)',
        'url': SUPABASE_URL,
        'database_url': DATABASE_URL[:50] + "..." if DATABASE_URL and len(DATABASE_URL) > 50 else DATABASE_URL,
        'persistent': True,
        'railway_compatible': True,
        'production_ready': True
    } 