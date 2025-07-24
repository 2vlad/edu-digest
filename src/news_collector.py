#!/usr/bin/env python3
"""
Основной модуль сбора новостей
Центральный модуль для сбора, обработки и публикации новостного дайджеста
ТОЛЬКО SUPABASE - БЕЗ SQLite FALLBACK
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

# Импорты внутренних модулей
from .database import (ChannelsDB, ProcessedMessagesDB, SettingsDB, 
                      create_connection)
from .claude_summarizer import get_claude_summarizer
from .telegram_bot import get_telegram_bot, TelegramChannelReader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/news_collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NewsCollector:
    """Основной класс для сбора и обработки новостного дайджеста"""
    
    def __init__(self):
        self.claude_summarizer = None
        self.telegram_bot = None
        self.channel_reader = None
        self.run_id = None
        
        # Настройки из базы данных
        self.max_news_count = 10
        self.hours_lookback = 12
        self.target_channel = "@vestnik_edtech"
        
    async def initialize(self):
        """Инициализация всех компонентов"""
        try:
            logger.info("🚀 Инициализация NewsCollector...")
            
            # Инициализация компонентов сбора
            self.claude_summarizer = await get_claude_summarizer()
            self.telegram_bot = await get_telegram_bot() 
            self.channel_reader = TelegramChannelReader()
            
            # Загружаем настройки из базы данных
            await self._load_settings()
            
            # Создаем запись о запуске
            self.run_id = self._create_run_log()
            
            logger.info("✅ NewsCollector инициализирован успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации NewsCollector: {e}")
            return False
    
    async def _load_settings(self):
        """Загрузка настроек из базы данных"""
        self.max_news_count = int(SettingsDB.get_setting('max_news_count', '10'))
        self.hours_lookback = int(SettingsDB.get_setting('hours_lookback', '12'))
        self.target_channel = SettingsDB.get_setting('target_channel', '@vestnik_edtech')
        
        logger.info(f"📊 Настройки: max_news={self.max_news_count}, lookback={self.hours_lookback}h, target={self.target_channel}")
    
    def _create_run_log(self) -> int:
        """Создание записи о запуске сбора новостей"""
        conn = create_connection()
        if conn is None:
            logger.warning("⚠️ PostgreSQL недоступен, пропускаем создание лога запуска")
            return None
            
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO run_logs (started_at, status) 
                VALUES (CURRENT_TIMESTAMP, 'started')
                RETURNING id
            ''')
            result = cursor.fetchone()
            run_id = result['id']
            logger.info(f"📝 Создан лог запуска #{run_id}")
            return run_id
        except Exception as e:
            logger.error(f"❌ Ошибка создания лога запуска: {e}")
            return None
    
    def _update_run_log(self, status: str, channels_processed: int = 0, 
                       messages_collected: int = 0, news_published: int = 0, 
                       error_message: str = None):
        """Обновление записи о запуске"""
        if not self.run_id:
            return
            
        conn = create_connection()
        if conn is None:
            logger.warning("⚠️ PostgreSQL недоступен, пропускаем обновление лога запуска")
            return
            
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE run_logs SET 
                    completed_at = CURRENT_TIMESTAMP,
                    status = %s,
                    channels_processed = %s,
                    messages_collected = %s,
                    news_published = %s,
                    error_message = %s
                WHERE id = %s
            ''', (status, channels_processed, messages_collected, 
                  news_published, error_message, self.run_id))
        except Exception as e:
            logger.error(f"❌ Ошибка обновления лога запуска: {e}")
    
    async def collect_news(self) -> Dict[str, Any]:
        """Сбор новых сообщений из всех активных каналов"""
        try:
            logger.info("📡 Начинаем сбор новостей из каналов...")
            
            # Получаем список активных каналов
            channels = ChannelsDB.get_active_channels()
            if not channels:
                logger.warning("⚠️ Нет активных каналов для мониторинга")
                return {"success": False, "error": "Нет активных каналов"}
            
            logger.info(f"📺 Найдено {len(channels)} активных каналов")
            
            all_messages = []
            channels_processed = 0
            
            # Обрабатываем каждый канал
            for channel in channels:
                try:
                    logger.info(f"🔍 Обрабатываем канал {channel['username']} (приоритет: {channel['priority']})")
                    
                    # Получаем реальные сообщения через Telethon
                    try:
                        logger.info(f"📡 Получение реальных данных из {channel['username']}")
                        from .telegram_reader import get_telegram_reader
                        real_reader = await get_telegram_reader()
                        
                        if not real_reader:
                            logger.warning(f"⚠️ Не удалось инициализировать Telegram reader для {channel['username']}, пропускаем")
                            continue
                            
                        if not real_reader.initialized:
                            logger.warning(f"⚠️ Telegram reader не инициализирован для {channel['username']}, пропускаем")
                            continue
                            
                        # Получаем новые сообщения
                        messages = await real_reader.get_channel_messages(channel['username'], limit=50, hours_lookback=self.hours_lookback)
                        
                        if not messages:
                            logger.info(f"ℹ️ {channel['username']}: новых сообщений не найдено, пропускаем")
                            continue
                            
                    except Exception as reader_error:
                        logger.warning(f"⚠️ Ошибка получения данных из {channel['username']}: {reader_error} - пропускаем канал")
                        continue
                    
                    # Фильтруем новые сообщения
                    new_messages = []
                    for msg in messages:
                        msg['channel_id'] = channel['id']
                        msg['priority'] = channel['priority']
                        msg['channel_display'] = channel.get('display_name', channel['username'])
                        
                        # Проверяем, не было ли сообщение уже обработано
                        if not ProcessedMessagesDB.is_message_processed(channel['id'], msg['id']):
                            new_messages.append(msg)
                    
                    all_messages.extend(new_messages)
                    channels_processed += 1
                    
                    logger.info(f"✅ {channel['username']}: найдено {len(new_messages)} новых сообщений")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки канала {channel['username']}: {e}")
                    continue
            
            # Сортируем по приоритету канала и времени
            all_messages.sort(key=lambda x: (-x['priority'], -x['date'].timestamp()))
            
            logger.info(f"📊 Всего собрано {len(all_messages)} новых сообщений из {channels_processed} каналов")
            
            return {
                "success": True,
                "messages": all_messages,
                "channels_processed": channels_processed
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка сбора новостей: {e}")
            return {"success": False, "error": str(e)}
    
    async def filter_and_prioritize(self, messages: List[Dict]) -> List[Dict]:
        """Фильтрация и приоритизация сообщений"""
        if not messages:
            logger.warning("⚠️ Нет сообщений для фильтрации")
            return []
        
        logger.info(f"🎯 Фильтрация {len(messages)} сообщений...")
        
        # Фильтрация по времени (последние N часов) - используем UTC
        from datetime import timezone
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=self.hours_lookback)
        time_filtered = []
        
        for msg in messages:
            if msg['date'] >= time_threshold:
                time_filtered.append(msg)
        
        logger.info(f"⏰ После фильтрации по времени: {len(time_filtered)} сообщений")
        
        # Фильтрация по релевантности (EdTech ключевые слова)
        edtech_keywords = [
            'образован', 'учеб', 'студент', 'университет', 'школ', 'онлайн-курс',
            'edtech', 'образовательн', 'дистанционн', 'цифров', 'технолог',
            'платформ', 'стартап', 'инновац', 'искусственный интеллект', 'ai',
            'машинное обучение', 'данные', 'аналитик', 'курс', 'обучени'
        ]
        
        content_filtered = []
        for msg in time_filtered:
            text_lower = msg['text'].lower()
            relevance_score = sum(1 for keyword in edtech_keywords if keyword in text_lower)
            
            if relevance_score > 0:  # Минимум одно EdTech ключевое слово
                msg['relevance_score'] = relevance_score
                content_filtered.append(msg)
        
        logger.info(f"🎯 После фильтрации по релевантности: {len(content_filtered)} сообщений")
        
        # Сортировка по комбинированному приоритету
        def priority_score(msg):
            return (
                msg['priority'] * 10 +  # Приоритет канала (0-100)
                msg.get('relevance_score', 0) * 5 +  # Релевантность (0-50+)
                min(msg.get('views', 0) or 0, 1000) / 100  # Популярность (0-10)
            )
        
        content_filtered.sort(key=priority_score, reverse=True)
        
        # Ограничиваем количество
        final_messages = content_filtered[:self.max_news_count]
        
        logger.info(f"📋 Финальная выборка: {len(final_messages)} сообщений (макс. {self.max_news_count})")
        
        return final_messages
    
    async def summarize_messages(self, messages: List[Dict]) -> List[Dict]:
        """Суммаризация сообщений с помощью Claude AI"""
        if not messages:
            logger.warning("⚠️ Нет сообщений для суммаризации")
            return []
        
        logger.info(f"🤖 Суммаризация {len(messages)} сообщений...")
        
        summarized_messages = []
        
        for msg in messages:
            try:
                # Суммаризируем текст сообщения
                if self.claude_summarizer:
                    result = await self.claude_summarizer.summarize_message(
                        msg['text'], 
                        msg.get('channel_display', msg.get('channel', ''))
                    )
                    if result['success']:
                        msg['summary'] = result['summary']
                        msg['summary_quality'] = result.get('quality_score', 8)
                    else:
                        msg['summary'] = result['summary']  # Fallback summary
                        msg['summary_quality'] = 3
                else:
                    # Fallback: берем первые 150 символов
                    msg['summary'] = msg['text'][:150] + "..." if len(msg['text']) > 150 else msg['text']
                    msg['summary_quality'] = 5
                
                summarized_messages.append(msg)
                
            except Exception as e:
                logger.error(f"❌ Ошибка суммаризации сообщения {msg['id']}: {e}")
                # Добавляем сообщение без суммаризации
                msg['summary'] = msg['text'][:150] + "..." if len(msg['text']) > 150 else msg['text']
                msg['summary_quality'] = 3
                summarized_messages.append(msg)
        
        logger.info(f"✅ Суммаризировано {len(summarized_messages)} сообщений")
        return summarized_messages
    
    def format_digest(self, messages: List[Dict]) -> str:
        """Форматирование дайджеста для публикации"""
        if not messages:
            return "📰 Новых новостей EdTech сегодня не найдено."
        
        logger.info(f"📝 Форматирование дайджеста из {len(messages)} сообщений...")
        
        # Определяем время суток для заголовка
        from datetime import timezone
        current_hour = datetime.now(timezone.utc).hour + 3  # MSK
        digest_type = "Утренний" if 9 <= current_hour < 15 else "Вечерний"
        
        digest_lines = []
        # Убираем звездочки у тайтла
        digest_lines.append(f"{digest_type} дайджест")
        digest_lines.append("")  # Отбивка после заголовка
        
        # Форматируем сообщения
        for i, msg in enumerate(messages):
            # Используем суммаризацию Claude или оригинальный текст
            if 'summary' in msg and msg['summary']:
                summary = msg['summary']
            else:
                # Fallback к оригинальному тексту (более развернутый)
                text = msg['text']
                
                # Извлекаем первые два предложения или первые 200 символов
                sentences_end = []
                for idx, char in enumerate(text):
                    if char in '.!?' and idx < 300:
                        sentences_end.append(idx)
                        if len(sentences_end) >= 2:  # Берем два предложения
                            break
                
                if len(sentences_end) >= 2:
                    summary = text[:sentences_end[1] + 1].strip()
                elif len(sentences_end) == 1:
                    summary = text[:sentences_end[0] + 1].strip()
                else:
                    # Берем первые слова до 150 символов
                    summary = text[:150].strip()
                    if len(text) > 150:
                        summary += '...'
                
                # Убираем лишние символы и ссылки
                summary = summary.replace('**', '').replace('*', '')
                summary = summary.split('\n')[0]  # Берем только первую строку
                summary = summary.split('[')[0]  # Убираем ссылки в квадратных скобках
                summary = summary.split('(http')[0]  # Убираем URL
                summary = summary.strip()
            
            # Получаем название канала и создаем ссылку
            channel_display = msg.get('channel_display', msg.get('channel', 'Unknown'))
            channel_username = msg.get('channel', '')
            
            # Создаем ссылку на канал (убираем @ для правильной ссылки)
            clean_username = channel_username.lstrip('@') if channel_username else 'unknown'
            channel_link = f"https://t.me/{clean_username}"
            
            # Форматируем строку: — Заголовок ([Канал](ссылка))
            digest_lines.append(f"— {summary} ([{channel_display}]({channel_link}))")
            
            # Добавляем отбивку между новостями (кроме последней)
            if i < len(messages) - 1:
                digest_lines.append("")
        
        # Добавляем случайный стильный эмодзи в конце
        import random
        style_emojis = ['🍿', '🎯', '🚀', '✨', '💡', '🔥', '⚡', '🌟', '💫', '🎪', '🎨', '🎭']
        random_emoji = random.choice(style_emojis)
        
        digest_lines.append("")
        digest_lines.append(random_emoji)
        
        digest_text = "\n".join(digest_lines)
        
        # Проверяем длину для Telegram (максимум 4096 символов)
        if len(digest_text) > 4096:
            logger.warning(f"⚠️ Дайджест слишком длинный ({len(digest_text)} символов), обрезаем...")
            # Обрезаем сообщения, оставляя эмодзи
            lines_without_emoji = digest_lines[:-2]
            while len("\n".join(lines_without_emoji + ["", random_emoji])) > 4000:
                lines_without_emoji.pop()
            digest_text = "\n".join(lines_without_emoji + ["", random_emoji])
        
        logger.info(f"✅ Дайджест сформирован: {len(digest_text)} символов")
        return digest_text
    
    async def validate_and_publish(self, digest: str, messages: List[Dict]) -> Dict[str, Any]:
        """Валидация и публикация дайджеста"""
        try:
            logger.info("🔍 Валидация дайджеста перед публикацией...")
            
            # Валидация содержания
            validation_errors = []
            
            if len(digest.strip()) < 50:
                validation_errors.append("Дайджест слишком короткий")
            
            if len(digest) > 4096:
                validation_errors.append("Дайджест превышает лимит Telegram (4096 символов)")
            
            if not messages:
                validation_errors.append("Нет новостей для публикации")
            
            # Проверяем качество суммаризации
            if messages:
                avg_quality = sum(msg.get('summary_quality', 0) for msg in messages) / len(messages)
                if avg_quality < 5:
                    validation_errors.append(f"Низкое качество суммаризации ({avg_quality:.1f}/10)")
            
            if validation_errors:
                logger.warning(f"⚠️ Найдены проблемы валидации: {'; '.join(validation_errors)}")
            
            # Публикация в Telegram
            logger.info(f"📡 Публикуем дайджест в {self.target_channel}...")
            
            publication_success = await self.telegram_bot.send_digest(digest)
            
            if publication_success:
                logger.info("✅ Дайджест успешно опубликован!")
                
                # Отмечаем сообщения как обработанные
                for msg in messages:
                    ProcessedMessagesDB.mark_message_processed(
                        msg['channel_id'], 
                        msg['id'],
                        msg['text'],
                        msg.get('summary', '')
                    )
                
                return {
                    "success": True,
                    "published": True,
                    "validation_errors": validation_errors,
                    "news_count": len(messages),
                    "digest_length": len(digest)
                }
            else:
                logger.error("❌ Ошибка публикации в Telegram")
                return {
                    "success": False,
                    "published": False,
                    "error": "Ошибка публикации в Telegram",
                    "validation_errors": validation_errors
                }
        
        except Exception as e:
            logger.error(f"❌ Ошибка валидации и публикации: {e}")
            return {
                "success": False,
                "published": False,
                "error": str(e)
            }
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """Полный цикл сбора, обработки и публикации новостей"""
        start_time = datetime.now()
        logger.info(f"🚀 Запуск полного цикла сбора новостей в {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Инициализация компонентов
            if not await self.initialize():
                raise Exception("Ошибка инициализации")
            
            # Сбор новостей
            collection_result = await self.collect_news()
            if not collection_result["success"]:
                raise Exception(f"Ошибка сбора: {collection_result['error']}")
            
            messages = collection_result["messages"]
            channels_processed = collection_result["channels_processed"]
            
            # Фильтрация и приоритизация
            filtered_messages = await self.filter_and_prioritize(messages)
            
            # Суммаризация
            summarized_messages = await self.summarize_messages(filtered_messages)
            
            # Форматирование
            digest = self.format_digest(summarized_messages)
            
            # Валидация и публикация
            publish_result = await self.validate_and_publish(digest, summarized_messages)
            
            # Финальный результат
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            result = {
                "success": publish_result["success"],
                "execution_time": execution_time,
                "channels_processed": channels_processed,
                "messages_collected": len(messages),
                "messages_filtered": len(filtered_messages),
                "messages_summarized": len(summarized_messages),
                "news_published": len(summarized_messages) if publish_result["published"] else 0,
                "digest_length": len(digest),
                "validation_errors": publish_result.get("validation_errors", []),
                "published": publish_result["published"]
            }
            
            # Обновляем лог запуска
            status = "completed" if result["success"] else "failed"
            self._update_run_log(
                status=status,
                channels_processed=result["channels_processed"],
                messages_collected=result["messages_collected"],
                news_published=result["news_published"],
                error_message=publish_result.get("error") if not result["success"] else None
            )
            
            logger.info(f"🎉 Полный цикл завершен за {execution_time:.1f}с:")
            logger.info(f"   📊 Обработано каналов: {result['channels_processed']}")
            logger.info(f"   📝 Собрано сообщений: {result['messages_collected']}")
            logger.info(f"   🎯 Отфильтровано: {result['messages_filtered']}")
            logger.info(f"   🤖 Суммаризировано: {result['messages_summarized']}")
            logger.info(f"   📰 Опубликовано новостей: {result['news_published']}")
            logger.info(f"   ✅ Статус: {'Успешно' if result['success'] else 'Ошибка'}")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.error(f"❌ Ошибка полного цикла: {e}")
            
            # Обновляем лог запуска с ошибкой
            self._update_run_log(
                status="failed",
                error_message=str(e)
            )
            
            return {
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "channels_processed": 0,
                "messages_collected": 0,
                "messages_filtered": 0,
                "messages_summarized": 0,
                "news_published": 0
            }

# Основная функция для запуска из командной строки
async def main():
    """Основная функция для запуска сбора новостей"""
    collector = NewsCollector()
    result = await collector.run_full_cycle()
    
    if result["success"]:
        print("✅ Сбор новостей завершен успешно!")
        exit(0)
    else:
        print(f"❌ Ошибка сбора новостей: {result['error']}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())