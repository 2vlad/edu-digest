import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio

from telegram import Bot
from telegram.error import TelegramError

from .config import TELEGRAM_BOT_TOKEN, TARGET_CHANNEL
from .database import ChannelsDB, ProcessedMessagesDB

# Настройка логирования
import os
os.makedirs('logs', exist_ok=True)  # Создаем папку logs если не существует
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TelegramBot:
    """Класс для работы с Telegram Bot API (публикация дайджестов)"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = None
        self.initialized = False
        
    async def initialize(self):
        """Инициализация бота"""
        try:
            if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_bot_token":
                raise ValueError("TELEGRAM_BOT_TOKEN не настроен в .env")
                
            self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
            
            # Проверяем что бот работает
            bot_info = await self.bot.get_me()
            logger.info(f"Бот инициализирован: @{bot_info.username}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации бота: {e}")
            return False
    
    async def test_bot_connection(self) -> Dict:
        """Тестирование подключения бота"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                return {"status": "error", "message": "Не удалось инициализировать бота"}
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            
            # Проверяем доступ к целевому каналу
            try:
                chat = await self.bot.get_chat(TARGET_CHANNEL)
                channel_access = {
                    "accessible": True,
                    "title": chat.title,
                    "type": chat.type,
                    "member_count": getattr(chat, 'member_count', None)
                }
            except TelegramError as e:
                channel_access = {
                    "accessible": False,
                    "error": str(e)
                }
            
            return {
                "status": "success",
                "bot_info": {
                    "username": bot_info.username,
                    "first_name": bot_info.first_name,
                    "id": bot_info.id
                },
                "target_channel": TARGET_CHANNEL,
                "channel_access": channel_access
            }
            
        except Exception as e:
            logger.error(f"Ошибка тестирования бота: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_digest(self, digest_text: str) -> bool:
        """Отправка дайджеста в канал"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                logger.error("Бот не инициализирован")
                return False
            
            # Отправляем сообщение (временно без parse_mode для устранения ошибок)
            message = await self.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=digest_text,
                disable_web_page_preview=True
            )
            
            logger.info(f"Дайджест опубликован: {message.message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки дайджеста: {e}")
            return False
    
    async def send_test_message(self) -> bool:
        """Отправка тестового сообщения"""
        test_text = f"🔧 Тестовое сообщение от EdTech News Bot\n\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return await self.send_digest(test_text)

# Для обратной совместимости и работы с User API через Telethon
class TelegramChannelReader:
    """Упрощенная версия для чтения каналов (без авторизации)"""
    
    @staticmethod
    async def simulate_channel_messages(channel_username: str, count: int = 5) -> List[Dict]:
        """Симуляция получения сообщений из канала (для тестирования)"""
        # Это заглушка для тестирования без реальной авторизации
        messages = []
        base_time = datetime.now()
        
        for i in range(count):
            messages.append({
                'id': 1000 + i,
                'date': base_time - timedelta(hours=i),
                'text': f"Тестовое сообщение {i+1} из канала {channel_username}. "
                       f"Это пример новости об образовательных технологиях, которая "
                       f"будет обработана системой автоматического дайджеста.",
                'channel': channel_username,
                'link': f"https://t.me/{channel_username.replace('@', '')}/{1000 + i}",
                'media_type': None,
                'external_links': [],
                'views': 100 + i * 10,
                'forwards': i * 2,
                'is_reply': False,
                'sender_id': 12345,
                'channel_id': 1,  # Будет определено из БД
                'priority': 5
            })
        
        return messages
    
    async def test_channel_reading(self) -> Dict:
        """Тестирование чтения каналов"""
        try:
            channels = ChannelsDB.get_active_channels()
            
            if not channels:
                return {
                    "status": "warning", 
                    "message": "Нет активных каналов в базе данных"
                }
            
            results = {}
            for channel in channels[:3]:  # Тестируем первые 3 канала
                username = channel['username']
                
                # Симулируем получение сообщений
                messages = await self.simulate_channel_messages(username, 3)
                
                results[username] = {
                    "accessible": True,
                    "message_count": len(messages),
                    "sample_messages": [
                        {
                            "id": msg['id'],
                            "date": msg['date'].strftime('%Y-%m-%d %H:%M:%S'),
                            "text_preview": msg['text'][:100] + "..."
                        } for msg in messages[:2]
                    ]
                }
            
            return {
                "status": "success",
                "channels_tested": len(results),
                "results": results,
                "note": "Используется симуляция данных. Для реального чтения каналов требуется авторизация Telethon"
            }
            
        except Exception as e:
            logger.error(f"Ошибка тестирования каналов: {e}")
            return {"status": "error", "message": str(e)}

# Глобальный экземпляр бота
_bot_instance = None

async def get_telegram_bot() -> TelegramBot:
    """Получение инициализированного экземпляра бота"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot()
        await _bot_instance.initialize()
    return _bot_instance