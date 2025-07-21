import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.messages import GetHistoryRequest

from .config import TELEGRAM_API_ID, TELEGRAM_API_HASH
from .database import ChannelsDB, ProcessedMessagesDB

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TelegramNewsCollector:
    """Класс для работы с Telegram API через Telethon"""
    
    def __init__(self, session_name: str = "edu_digest_bot"):
        """Инициализация Telegram клиента"""
        self.session_name = session_name
        self.client = None
        self.is_authorized = False
        
    async def initialize_client(self):
        """3.1. Настройка Telethon клиента и аутентификация"""
        try:
            self.client = TelegramClient(
                self.session_name,
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH
            )
            
            await self.client.start()
            
            # Проверка авторизации
            if await self.client.is_user_authorized():
                self.is_authorized = True
                me = await self.client.get_me()
                logger.info(f"Успешная авторизация как: {me.first_name} (@{me.username})")
            else:
                logger.error("Клиент не авторизован. Требуется авторизация через номер телефона.")
                self.is_authorized = False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram клиента: {e}")
            raise
    
    async def authorize_with_phone(self, phone_number: str):
        """Авторизация с помощью номера телефона (для первичной настройки)"""
        try:
            await self.client.send_code_request(phone_number)
            logger.info(f"Код отправлен на номер {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки кода: {e}")
            return False
    
    async def verify_code(self, phone_number: str, code: str):
        """Подтверждение кода авторизации"""
        try:
            await self.client.sign_in(phone_number, code)
            self.is_authorized = True
            logger.info("Авторизация успешно завершена")
            return True
        except SessionPasswordNeededError:
            logger.info("Требуется двухфакторная аутентификация")
            return "2fa_required"
        except PhoneCodeInvalidError:
            logger.error("Неверный код подтверждения")
            return False
        except Exception as e:
            logger.error(f"Ошибка подтверждения кода: {e}")
            return False
    
    async def sign_in_with_password(self, password: str):
        """Вход с паролем двухфакторной аутентификации"""
        try:
            await self.client.sign_in(password=password)
            self.is_authorized = True
            logger.info("Авторизация с 2FA успешно завершена")
            return True
        except Exception as e:
            logger.error(f"Ошибка 2FA авторизации: {e}")
            return False
    
    async def get_channel_info(self, channel_username: str) -> Optional[Dict]:
        """Получение информации о канале"""
        if not self.is_authorized:
            logger.error("Клиент не авторизован")
            return None
        
        try:
            entity = await self.client.get_entity(channel_username)
            
            return {
                'id': entity.id,
                'username': channel_username,
                'title': entity.title if hasattr(entity, 'title') else channel_username,
                'access_hash': entity.access_hash if hasattr(entity, 'access_hash') else None,
                'participants_count': entity.participants_count if hasattr(entity, 'participants_count') else None,
                'type': 'channel' if isinstance(entity, Channel) else 'chat' if isinstance(entity, Chat) else 'user'
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о канале {channel_username}: {e}")
            return None
    
    async def get_recent_messages(self, channel_username: str, hours_back: int = 12, limit: int = 100) -> List[Dict]:
        """3.2. Получение сообщений из каналов"""
        if not self.is_authorized:
            logger.error("Клиент не авторизован")
            return []
        
        try:
            entity = await self.client.get_entity(channel_username)
            
            # Время с которого собираем сообщения
            time_limit = datetime.now() - timedelta(hours=hours_back)
            
            messages = []
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.date < time_limit:
                    break
                
                # 3.3. Обработка разных типов контента
                message_data = await self._process_message_content(message, channel_username)
                if message_data:
                    messages.append(message_data)
            
            logger.info(f"Получено {len(messages)} сообщений из {channel_username}")
            return messages
            
        except Exception as e:
            logger.error(f"Ошибка получения сообщений из {channel_username}: {e}")
            return []
    
    async def _process_message_content(self, message, channel_username: str) -> Optional[Dict]:
        """3.3. Обработка разных типов контента (текст, медиа, ссылки)"""
        try:
            # Пропускаем сообщения без текста
            if not message.text and not message.caption:
                return None
            
            text_content = message.text or message.caption or ""
            
            # Извлечение ссылок из сообщения
            links = []
            if message.entities:
                for entity in message.entities:
                    if hasattr(entity, 'url'):
                        links.append(entity.url)
            
            # Информация о медиа
            media_type = None
            if message.media:
                media_type = type(message.media).__name__
            
            # Формирование ссылки на сообщение
            message_link = f"https://t.me/{channel_username.replace('@', '')}/{message.id}"
            
            return {
                'id': message.id,
                'date': message.date,
                'text': text_content,
                'channel': channel_username,
                'link': message_link,
                'media_type': media_type,
                'external_links': links,
                'views': message.views if hasattr(message, 'views') else None,
                'forwards': message.forwards if hasattr(message, 'forwards') else None,
                'is_reply': message.reply_to is not None,
                'sender_id': message.sender_id
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения {message.id}: {e}")
            return None
    
    async def collect_new_messages_from_channels(self, hours_back: int = 12) -> List[Dict]:
        """3.4. Система отслеживания последних сообщений"""
        if not self.is_authorized:
            logger.error("Клиент не авторизован")
            return []
        
        try:
            # Получаем активные каналы из базы данных
            channels = ChannelsDB.get_active_channels()
            all_new_messages = []
            
            for channel in channels:
                channel_username = channel['username']
                last_message_id = channel['last_message_id']
                
                logger.info(f"Обрабатываем канал {channel_username}, последнее сообщение: {last_message_id}")
                
                try:
                    # Получаем новые сообщения
                    recent_messages = await self.get_recent_messages(
                        channel_username, 
                        hours_back=hours_back
                    )
                    
                    # Фильтруем только новые сообщения
                    new_messages = []
                    max_message_id = last_message_id
                    
                    for msg in recent_messages:
                        if msg['id'] > last_message_id:
                            # Проверяем, не было ли сообщение уже обработано
                            if not ProcessedMessagesDB.is_message_processed(channel['id'], msg['id']):
                                msg['channel_id'] = channel['id']
                                msg['priority'] = channel['priority']
                                new_messages.append(msg)
                                max_message_id = max(max_message_id, msg['id'])
                    
                    # Обновляем ID последнего сообщения
                    if max_message_id > last_message_id:
                        ChannelsDB.update_last_message_id(channel['id'], max_message_id)
                    
                    all_new_messages.extend(new_messages)
                    logger.info(f"Найдено {len(new_messages)} новых сообщений в {channel_username}")
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки канала {channel_username}: {e}")
                    continue
            
            # Сортируем по приоритету канала и времени
            all_new_messages.sort(key=lambda x: (-x['priority'], -x['date'].timestamp()))
            
            logger.info(f"Всего собрано {len(all_new_messages)} новых сообщений")
            return all_new_messages
            
        except Exception as e:
            logger.error(f"Ошибка сбора новых сообщений: {e}")
            return []
    
    async def test_channel_access(self, channel_username: str) -> Dict[str, Any]:
        """Тестирование доступа к каналу"""
        if not self.is_authorized:
            return {"status": "error", "message": "Клиент не авторизован"}
        
        try:
            # Получаем информацию о канале
            channel_info = await self.get_channel_info(channel_username)
            if not channel_info:
                return {"status": "error", "message": "Канал не найден или недоступен"}
            
            # Пробуем получить последние сообщения
            recent_messages = await self.get_recent_messages(channel_username, hours_back=1, limit=5)
            
            return {
                "status": "success",
                "channel_info": channel_info,
                "recent_messages_count": len(recent_messages),
                "sample_messages": recent_messages[:2] if recent_messages else []
            }
            
        except Exception as e:
            logger.error(f"Ошибка тестирования канала {channel_username}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def disconnect(self):
        """Отключение от Telegram"""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            logger.info("Отключение от Telegram API")

# 3.5. Обработка ошибок API и логика повторных попыток
class TelegramErrorHandler:
    """Класс для обработки ошибок Telegram API"""
    
    @staticmethod
    async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
        """Повторная попытка с экспоненциальной задержкой"""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Все попытки исчерпаны. Последняя ошибка: {e}")
                    raise
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Попытка {attempt + 1} не удалась: {e}. Повтор через {delay}с")
                await asyncio.sleep(delay)

# Основная функция для использования в других модулях
async def get_telegram_collector() -> TelegramNewsCollector:
    """Получение настроенного Telegram клиента"""
    collector = TelegramNewsCollector()
    await collector.initialize_client()
    return collector