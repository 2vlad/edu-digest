#!/usr/bin/env python3
"""
Генератор ретроспективных дайджестов
Создает дайджесты за прошедшие дни для наполнения канала
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta, time, date
from typing import List, Dict, Optional

# Импортируем наши модули
sys.path.append('/Users/tovlad01/Dev/edu-digest')
from src.news_collector import NewsCollector
from src.telegram_reader import get_telegram_reader
from src.claude_summarizer import get_claude_summarizer
from src.telegram_bot import get_telegram_bot
from src.database import ChannelsDB

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_digests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HistoricalDigestGenerator:
    """Генератор исторических дайджестов"""
    
    def __init__(self):
        self.telegram_reader = None
        self.claude_summarizer = None
        self.telegram_bot = None
        self.channels_db = ChannelsDB()
        
    async def initialize(self):
        """Инициализация компонентов"""
        logger.info("🚀 Инициализация генератора исторических дайджестов...")
        
        self.telegram_reader = await get_telegram_reader()
        if not self.telegram_reader:
            raise Exception("Не удалось инициализировать Telegram reader")
            
        self.claude_summarizer = await get_claude_summarizer()
        self.telegram_bot = await get_telegram_bot()
        
        logger.info("✅ Все компоненты инициализированы")
        
    async def get_historical_messages(self, target_date: date, 
                                    start_hour: int, end_hour: int) -> List[Dict]:
        """
        Получение сообщений за конкретную дату и временной промежуток
        
        Args:
            target_date: Целевая дата
            start_hour: Начальный час (включительно)
            end_hour: Конечный час (исключительно)
        """
        logger.info(f"📅 Сбор сообщений за {target_date} с {start_hour}:00 до {end_hour}:00")
        
        # Получаем активные каналы
        channels = self.channels_db.get_active_channels()
        if not channels:
            logger.warning("⚠️ Нет активных каналов")
            return []
            
        logger.info(f"📡 Найдено {len(channels)} активных каналов")
        
        all_messages = []
        
        # Создаем временные границы в UTC (учитывая МСК = UTC+3)
        msk_start = datetime.combine(target_date, time(start_hour, 0))
        msk_end = datetime.combine(target_date, time(end_hour, 0))
        
        # Конвертируем в UTC
        utc_start = msk_start - timedelta(hours=3)
        utc_end = msk_end - timedelta(hours=3)
        
        logger.info(f"🕐 Временные границы UTC: {utc_start} - {utc_end}")
        
        for channel in channels:
            username = channel.get('username', '')
            if not username:
                continue
                
            try:
                logger.info(f"📱 Обрабатываем канал: {username}")
                
                # Используем новый метод для получения сообщений по диапазону дат
                messages = await self.telegram_reader.get_channel_messages_by_date_range(
                    username,
                    start_date=utc_start,
                    end_date=utc_end,
                    limit=200  # Увеличиваем лимит для исторических данных
                )
                
                logger.info(f"✅ {username}: найдено {len(messages)} сообщений в диапазоне")
                all_messages.extend(messages)
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки канала {username}: {e}")
                continue
        
        # Сортируем по времени (старые сначала)
        all_messages.sort(key=lambda x: x['date'])
        
        logger.info(f"📊 Всего собрано {len(all_messages)} сообщений за указанный период")
        return all_messages
    
    async def create_historical_digest(self, target_date: date, 
                                     digest_type: str, 
                                     start_hour: int, end_hour: int,
                                     publish: bool = True) -> Dict:
        """
        Создание исторического дайджеста
        
        Args:
            target_date: Дата дайджеста
            digest_type: Тип дайджеста (Утренний/Вечерний)
            start_hour: Начальный час сбора
            end_hour: Конечный час сбора
            publish: Публиковать ли дайджест
        """
        logger.info(f"📰 Создание {digest_type.lower()} дайджеста за {target_date}")
        
        # Получаем сообщения
        messages = await self.get_historical_messages(target_date, start_hour, end_hour)
        
        if not messages:
            logger.warning(f"⚠️ Нет сообщений для дайджеста {digest_type} за {target_date}")
            return {"success": False, "reason": "no_messages"}
        
        # Ограничиваем количество новостей (максимум 10)
        if len(messages) > 10:
            logger.info(f"📝 Ограничиваем количество новостей: {len(messages)} → 10")
            messages = messages[:10]
        
        # Суммаризируем сообщения
        logger.info(f"🤖 Суммаризация {len(messages)} сообщений...")
        summarized_messages = await self.claude_summarizer.summarize_batch(messages)
        
        if not summarized_messages:
            logger.warning("⚠️ Не удалось суммаризировать сообщения")
            return {"success": False, "reason": "summarization_failed"}
        
        # Форматируем дайджест с историческим заголовком
        digest_text = self.format_historical_digest(
            summarized_messages, target_date, digest_type
        )
        
        result = {
            "success": True,
            "date": target_date,
            "type": digest_type,
            "messages_count": len(summarized_messages),
            "digest_text": digest_text
        }
        
        # Публикуем если нужно
        if publish:
            logger.info(f"📡 Публикуем {digest_type.lower()} дайджест...")
            success = await self.telegram_bot.send_digest(digest_text)
            result["published"] = success
            
            if success:
                logger.info(f"✅ {digest_type} дайджест за {target_date} опубликован!")
            else:
                logger.error(f"❌ Ошибка публикации дайджеста")
        
        return result
    
    def format_historical_digest(self, messages: List[Dict], 
                                target_date: date, digest_type: str) -> str:
        """Форматирование исторического дайджеста"""
        
        # Форматируем дату по-русски
        months_ru = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа", 
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        
        date_str = f"{target_date.day} {months_ru[target_date.month]}"
        digest_title = f"{digest_type} дайджест {date_str}"
        
        digest_lines = []
        digest_lines.append(digest_title)
        digest_lines.append("")  # Отбивка после заголовка
        
        # Форматируем сообщения
        for i, msg in enumerate(messages):
            summary = msg.get('summary', msg['text'][:120] + '...')
            
            # Получаем название канала
            channel_name = msg.get('channel', '').replace('@', '')
            
            # Создаем ссылку на канал (без конкретного сообщения для исторических)
            channel_link = f"https://t.me/{channel_name}" if channel_name else ""
            
            if channel_link:
                news_line = f"• {summary} [{channel_name}]({channel_link})"
            else:
                news_line = f"• {summary}"
            
            digest_lines.append(news_line)
        
        # Добавляем эмодзи в конце
        digest_lines.append("")
        digest_lines.append("⚡")
        
        return "\n".join(digest_lines)

async def main():
    """Основная функция для генерации исторических дайджестов"""
    
    # Даты и временные промежутки для дайджестов
    digest_schedule = [
        # 22 июля
        (date(2025, 7, 22), "Утренний", 6, 12),   # 06:00-12:00 → Утренний
        (date(2025, 7, 22), "Вечерний", 12, 23),  # 12:00-23:00 → Вечерний
        
        # 23 июля  
        (date(2025, 7, 23), "Утренний", 6, 12),   # 06:00-12:00 → Утренний
        (date(2025, 7, 23), "Вечерний", 12, 23),  # 12:00-23:00 → Вечерний
        
        # 24 июля
        (date(2025, 7, 24), "Утренний", 6, 12),   # 06:00-12:00 → Утренний  
        (date(2025, 7, 24), "Вечерний", 12, 23),  # 12:00-23:00 → Вечерний
    ]
    
    generator = HistoricalDigestGenerator()
    
    try:
        await generator.initialize()
        
        logger.info("🎯 Начинаем генерацию 6 исторических дайджестов...")
        logger.info("=" * 60)
        
        results = []
        
        for i, (target_date, digest_type, start_hour, end_hour) in enumerate(digest_schedule, 1):
            logger.info(f"📅 Дайджест {i}/6: {digest_type} {target_date}")
            
            result = await generator.create_historical_digest(
                target_date=target_date,
                digest_type=digest_type, 
                start_hour=start_hour,
                end_hour=end_hour,
                publish=True  # Публикуем сразу
            )
            
            results.append(result)
            
            if result["success"]:
                logger.info(f"✅ Дайджест {i} создан: {result['messages_count']} новостей")
            else:
                logger.error(f"❌ Дайджест {i} не создан: {result['reason']}")
            
            # Пауза между публикациями (чтобы не спамить)
            if i < len(digest_schedule):
                logger.info("⏳ Пауза 10 секунд перед следующим дайджестом...")
                await asyncio.sleep(10)
        
        # Сводка результатов
        logger.info("=" * 60)
        logger.info("📊 СВОДКА РЕЗУЛЬТАТОВ:")
        
        successful = sum(1 for r in results if r["success"])
        logger.info(f"✅ Успешно создано: {successful}/{len(results)} дайджестов")
        
        for i, result in enumerate(results, 1):
            if result["success"]:
                logger.info(f"  {i}. {result['type']} {result['date']}: {result['messages_count']} новостей")
            else:
                logger.info(f"  {i}. Ошибка: {result['reason']}")
        
        logger.info("🎉 Генерация исторических дайджестов завершена!")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Генерация прервана пользователем")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")