#!/usr/bin/env python3
"""
Реальное чтение Telegram каналов с использованием Telethon
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaPhoto, MessageMediaDocument

try:
    from .config import TELEGRAM_API_ID, TELEGRAM_API_HASH
except ImportError:
    from config import TELEGRAM_API_ID, TELEGRAM_API_HASH

# Настройка логирования
import os
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_reader.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TelegramChannelReader:
    """Класс для чтения реальных Telegram каналов"""
    
    def __init__(self):
        self.client = None
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Инициализация Telethon клиента"""
        try:
            if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
                logger.error("❌ Отсутствуют TELEGRAM_API_ID или TELEGRAM_API_HASH")
                return False
            
            # Создаем клиент
            self.client = TelegramClient(
                'edu_digest_bot', 
                int(TELEGRAM_API_ID), 
                TELEGRAM_API_HASH
            )
            
            # Подключаемся
            await self.client.start()
            
            # Проверяем авторизацию
            me = await self.client.get_me()
            if me:
                logger.info(f"✅ Telethon клиент инициализирован: {me.first_name}")
                self.initialized = True
                return True
            else:
                logger.error("❌ Не удалось авторизоваться")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Telethon: {e}")
            return False
    
    async def get_channel_messages(self, channel_username: str, limit: int = 10, hours_lookback: int = 12) -> List[Dict]:
        """Получение реальных сообщений из канала"""
        try:
            if not self.initialized:
                logger.error("❌ Клиент не инициализирован")
                return []
            
            # Получаем entity канала
            try:
                entity = await self.client.get_entity(channel_username)
            except Exception as e:
                logger.error(f"❌ Не удалось найти канал {channel_username}: {e}")
                return []
            
            # Рассчитываем время отсечки
            time_limit = datetime.now() - timedelta(hours=hours_lookback)
            
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
            logger.error(f"❌ Ошибка получения сообщений из {channel_username}: {e}")
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
    
    if _reader_instance is None:
        _reader_instance = TelegramChannelReader()
        if not await _reader_instance.initialize():
            logger.error("❌ Не удалось инициализировать Telegram reader")
            return None
    
    return _reader_instance

# Функция для тестирования
async def test_channel_reading():
    """Тестовая функция для проверки чтения каналов"""
    reader = await get_telegram_reader()
    if not reader:
        print("❌ Не удалось создать reader")
        return
    
    test_channels = ['@edtexno', '@vc_edtech', '@rusedweek']
    
    for channel in test_channels:
        print(f"\n📡 Тестируем канал {channel}...")
        messages = await reader.get_channel_messages(channel, limit=3, hours_lookback=24)
        
        print(f"📊 Найдено {len(messages)} сообщений:")
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. {msg['text'][:100]}...")
            print(f"     🕒 {msg['date']} | 👀 {msg['views']} | 🔗 {msg['link']}")
    
    await reader.close()

if __name__ == "__main__":
    asyncio.run(test_channel_reading())