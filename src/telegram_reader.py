#!/usr/bin/env python3
"""
Реальное чтение Telegram каналов с использованием Telethon
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaPhoto, MessageMediaDocument

try:
    from .config import TELEGRAM_API_ID, TELEGRAM_API_HASH
except ImportError:
    from config import TELEGRAM_API_ID, TELEGRAM_API_HASH

# Настройка детального логирования
import os
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,  # Максимальный уровень детализации
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_reader.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Telegram Reader Module - REAL DATA ONLY MODE")

class TelegramChannelReader:
    """Класс для чтения реальных Telegram каналов"""
    
    def __init__(self):
        self.client = None
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Инициализация Telethon клиента"""
        try:
            logger.info("🔧 Initializing Telegram client...")
            logger.debug(f"🔍 Environment check:")
            logger.debug(f"   TELEGRAM_API_ID: {'✅ Set' if TELEGRAM_API_ID else '❌ Missing'}")
            logger.debug(f"   TELEGRAM_API_HASH: {'✅ Set' if TELEGRAM_API_HASH else '❌ Missing'}")
            
            if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
                logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют TELEGRAM_API_ID или TELEGRAM_API_HASH")
                logger.error("💡 Добавьте эти переменные в Railway Environment Variables:")
                logger.error("   TELEGRAM_API_ID=your_api_id")
                logger.error("   TELEGRAM_API_HASH=your_api_hash")
                logger.error("🔗 Получить можно на https://my.telegram.org/auth")
                return False
            
            # Создаем клиент
            logger.info("🔗 Creating Telethon client...")
            
            # Используем простое имя сессии
            # Используем статичное имя сессии, которое есть в файле
            self.client = TelegramClient(
                'railway_session', 
                int(TELEGRAM_API_ID), 
                TELEGRAM_API_HASH
            )
            
            # Подключаемся
            logger.info("🔗 Starting Telethon client connection...")
            
            # Проверяем наличие base64 сессии для Railway
            session_base64 = os.getenv('TELEGRAM_SESSION_BASE64')
            if session_base64:
                logger.info("🔐 Found TELEGRAM_SESSION_BASE64 in environment, decoding...")
                try:
                    import base64
                    session_data = base64.b64decode(session_base64)
                    with open('railway_session.session', 'wb') as f:
                        f.write(session_data)
                    logger.info("✅ Session file decoded and saved")
                except Exception as e:
                    logger.error(f"❌ Failed to decode session: {e}")
            
            # Проверяем если есть готовая сессия - используем её
            if os.path.exists('railway_session.session'):
                logger.info("🔑 Found existing session file, using it for user access")
                await self.client.start()
            else:
                # Fallback на bot token если нет сессии
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token:
                    logger.info("🤖 No session file, trying bot token...")
                    logger.warning("⚠️ Note: Bot API has limited access to channels")
                    logger.warning("⚠️ For full access, use TELEGRAM_SESSION_BASE64 environment variable")
                    try:
                        await self.client.start(bot_token=bot_token)
                        logger.info("✅ Telethon client started with bot token")
                    except Exception as e:
                        logger.error(f"❌ Bot token failed: {e}")
                        if "bot users is restricted" in str(e):
                            logger.error("💡 Bot users cannot read channels. You need a user session.")
                            logger.error("💡 Run create_session_for_railway.py locally and add TELEGRAM_SESSION_BASE64 to Railway")
                        return False
                else:
                    logger.error("❌ No session file and no bot token available")
                    return False
            logger.info("✅ Telethon client connection established")
            
            # Проверяем авторизацию
            logger.info("👤 Checking authorization...")
            me = await self.client.get_me()
            if me:
                logger.info(f"✅ Telethon client authorized successfully")
                logger.info(f"👤 User: {me.first_name} {me.last_name or ''} (@{me.username or 'no_username'})")
                logger.info(f"🆔 User ID: {me.id}")
                self.initialized = True
                return True
            else:
                logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться в Telegram")
                logger.error("💡 Возможные причины:")
                logger.error("   - Неверные TELEGRAM_API_ID или TELEGRAM_API_HASH")
                logger.error("   - Аккаунт заблокирован или ограничен")
                logger.error("   - Проблемы с сетевым подключением к Telegram API")
                return False
                
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА инициализации Telethon: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            if "api_id" in str(e) or "api_hash" in str(e):
                logger.error("💡 Проблема с API credentials - проверьте TELEGRAM_API_ID и TELEGRAM_API_HASH")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                logger.error("💡 Проблема с сетевым подключением к Telegram API")
            return False
    
    async def get_channel_messages(self, channel_username: str, limit: int = 10, hours_lookback: int = 12) -> List[Dict]:
        """Получение реальных сообщений из канала"""
        try:
            if not self.initialized:
                logger.error("❌ Клиент не инициализирован")
                return []
            
            # Очищаем username от символа @ если он есть
            clean_username = channel_username.lstrip('@')
            logger.info(f"🔍 Поиск канала: {channel_username} -> {clean_username}")
            
            # Получаем entity канала
            try:
                entity = await self.client.get_entity(clean_username)
                logger.info(f"✅ Канал найден: {entity.title if hasattr(entity, 'title') else clean_username}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось найти канал {channel_username}: {e} - пропускаем")
                return []
            
            # Рассчитываем время отсечки с UTC timezone  
            time_limit = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)
            
            messages = []
            async for message in self.client.iter_messages(entity, limit=limit):
                # Проверяем время
                if message.date < time_limit:
                    break
                
                # Пропускаем пустые сообщения
                if not message.text or len(message.text.strip()) < 50:
                    continue
                
                # Определяем тип медиа
                media_type = None
                if hasattr(message, 'media') and message.media:
                    if isinstance(message.media, MessageMediaPhoto):
                        media_type = 'photo'
                    elif isinstance(message.media, MessageMediaDocument):
                        media_type = 'document'
                    else:
                        media_type = 'other'
                
                # Формируем ссылку на сообщение
                link = f"https://t.me/{channel_username.replace('@', '')}/{message.id}"
                
                # Создаем объект сообщения
                msg_data = {
                    'id': message.id,
                    'date': message.date,
                    'text': message.text,
                    'channel': channel_username,
                    'link': link,
                    'media_type': media_type,
                    'views': getattr(message, 'views', 0),
                    'forwards': getattr(message, 'forwards', 0),
                    'is_reply': message.is_reply,
                    'sender_id': getattr(message, 'sender_id', None),
                    'reactions_count': 0,  # Можно добавить подсчет реакций
                    'external_links': self._extract_links(message.text) if message.text else []
                }
                
                messages.append(msg_data)
            
            logger.info(f"📥 Получено {len(messages)} сообщений из {channel_username}")
            return messages
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения сообщений из {channel_username}: {e} - пропускаем канал")
            return []
    
    async def get_channel_messages_by_date_range(self, channel_username: str, 
                                               start_date: datetime, end_date: datetime, 
                                               limit: int = 100) -> List[Dict]:
        """
        Получение сообщений из канала за определенный период времени
        
        Args:
            channel_username: Имя канала
            start_date: Начальная дата (включительно)
            end_date: Конечная дата (исключительно)
            limit: Максимальное количество сообщений для проверки
        """
        try:
            if not self.initialized:
                logger.error("❌ Клиент не инициализирован")
                return []
            
            # Очищаем username от символа @ если он есть
            clean_username = channel_username.lstrip('@')
            logger.info(f"🔍 Исторический поиск в канале: {channel_username} -> {clean_username}")
            logger.info(f"📅 Период: {start_date} - {end_date}")
            
            # Получаем entity канала
            try:
                entity = await self.client.get_entity(clean_username)
                logger.info(f"✅ Канал найден: {entity.title if hasattr(entity, 'title') else clean_username}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось найти канал {channel_username}: {e} - пропускаем")
                return []
            
            messages = []
            checked_count = 0
            
            async for message in self.client.iter_messages(entity, limit=limit):
                checked_count += 1
                
                # Убедимся, что дата сообщения имеет timezone
                msg_date = message.date
                if msg_date.tzinfo is None:
                    msg_date = msg_date.replace(tzinfo=timezone.utc)
                elif msg_date.tzinfo != timezone.utc:
                    msg_date = msg_date.astimezone(timezone.utc)
                    
                # Убедимся, что даты для сравнения тоже имеют timezone
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                
                # Если сообщение старше конечной даты, прекращаем поиск
                if msg_date < start_date:
                    logger.info(f"📊 Достигли начала периода поиска, проверено {checked_count} сообщений")
                    break
                
                # Если сообщение в нужном диапазоне времени
                if start_date <= msg_date < end_date:
                    # Пропускаем пустые сообщения
                    if not message.text or len(message.text.strip()) < 50:
                        continue
                    
                    # Определяем тип медиа
                    media_type = None
                    if hasattr(message, 'media') and message.media:
                        if isinstance(message.media, MessageMediaPhoto):
                            media_type = 'photo'
                        elif isinstance(message.media, MessageMediaDocument):
                            media_type = 'document'
                        else:
                            media_type = 'other'
                    
                    # Формируем ссылку на сообщение
                    link = f"https://t.me/{channel_username.replace('@', '')}/{message.id}"
                    
                    # Создаем объект сообщения
                    msg_data = {
                        'id': message.id,
                        'date': msg_date,
                        'text': message.text,
                        'channel': channel_username,
                        'link': link,
                        'media_type': media_type,
                        'views': getattr(message, 'views', 0),
                        'forwards': getattr(message, 'forwards', 0),
                        'is_reply': message.is_reply,
                        'sender_id': getattr(message, 'sender_id', None),
                        'reactions_count': 0,
                        'external_links': self._extract_links(message.text) if message.text else []
                    }
                    
                    messages.append(msg_data)
            
            logger.info(f"📥 Получено {len(messages)} сообщений из {channel_username} за период {start_date.date()} - {end_date.date()}")
            return messages
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения исторических сообщений из {channel_username}: {e}")
            return []
    
    def _extract_links(self, text: str) -> List[str]:
        """Извлечение внешних ссылок из текста"""
        import re
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        return url_pattern.findall(text)
    
    async def close(self):
        """Закрытие соединения"""
        if self.client:
            await self.client.disconnect()
            logger.info("🔌 Telethon клиент отключен")

# Глобальный экземпляр для переиспользования
_reader_instance = None

async def get_telegram_reader() -> TelegramChannelReader:
    """Получение инициализированного экземпляра читателя каналов"""
    global _reader_instance
    
    # Always create a fresh instance to avoid event loop conflicts
    if _reader_instance is not None:
        logger.info("🔄 Closing existing Telegram reader to prevent event loop conflicts...")
        try:
            await _reader_instance.close()
        except:
            pass
        _reader_instance = None
    
    logger.info("🔧 Creating new Telegram reader instance...")
    _reader_instance = TelegramChannelReader()
    try:
        logger.info("🔗 Initializing Telegram reader...")
        init_result = await _reader_instance.initialize()
        logger.info(f"📊 Initialization result: {init_result}")
        if not init_result:
            logger.error("❌ Не удалось инициализировать Telegram reader")
            _reader_instance = None
            return None
    except Exception as e:
        logger.error(f"❌ Exception during Telegram reader initialization: {e}")
        logger.error(f"❌ Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        _reader_instance = None
        return None
    
    return _reader_instance

# Функция для тестирования
async def test_channel_reading():
    """Тестовая функция для проверки чтения каналов"""
    reader = await get_telegram_reader()
    if not reader:
        print("❌ Не удалось создать reader")
        return
    
    # Получаем каналы из базы данных вместо хардкода
    try:
        from .database import ChannelsDB
        channels = ChannelsDB().get_active_channels()
        test_channels = [ch.get('username', '') for ch in channels[:3]]  # Первые 3 канала
        if not test_channels:
            print("❌ Нет активных каналов в базе данных")
            return
    except Exception as e:
        print(f"❌ Ошибка получения каналов из БД: {e}")
        print("💡 Используем пример реального канала...")
        test_channels = ['@habr_career']  # Известный существующий канал
    
    for channel in test_channels:
        if not channel:
            continue
        print(f"\n📡 Тестируем канал {channel}...")
        messages = await reader.get_channel_messages(channel, limit=3, hours_lookback=24)
        
        print(f"📊 Найдено {len(messages)} сообщений:")
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. {msg['text'][:100]}...")
            print(f"     🕒 {msg['date']} | 👀 {msg['views']} | 🔗 {msg['link']}")
    
    await reader.close()

if __name__ == "__main__":
    asyncio.run(test_channel_reading())