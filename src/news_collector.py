#!/usr/bin/env python3
"""
Task 5: Основной модуль сбора новостей
Центральный модуль для сбора, обработки и публикации новостного дайджеста
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

# Импорты внутренних модулей
from .database import (ChannelsDB, ProcessedMessagesDB, SettingsDB, 
                      create_connection, sqlite3)
from .claude_summarizer import get_claude_summarizer
from .telegram_bot import get_telegram_bot, TelegramChannelReader

# Настройка логирования
import os
os.makedirs('logs', exist_ok=True)  # Создаем папку logs если не существует
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
    """5.1-5.7: Основной класс для сбора и обработки новостного дайджеста"""
    
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
            
            # 5.1. Инициализация компонентов сбора
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
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO run_logs (started_at, status) 
                VALUES (CURRENT_TIMESTAMP, 'started')
            ''')
            conn.commit()
            run_id = cursor.lastrowid
            logger.info(f"📝 Создан лог запуска #{run_id}")
            return run_id
        finally:
            conn.close()
    
    def _update_run_log(self, status: str, channels_processed: int = 0, 
                       messages_collected: int = 0, news_published: int = 0, 
                       error_message: str = None):
        """Обновление записи о запуске"""
        if not self.run_id:
            return
            
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE run_logs SET 
                    completed_at = CURRENT_TIMESTAMP,
                    status = ?,
                    channels_processed = ?,
                    messages_collected = ?,
                    news_published = ?,
                    error_message = ?
                WHERE id = ?
            ''', (status, channels_processed, messages_collected, 
                  news_published, error_message, self.run_id))
            conn.commit()
        finally:
            conn.close()
    
    async def collect_news(self) -> Dict[str, Any]:
        """5.2. Сбор новых сообщений из всех активных каналов"""
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
                    
                    # Для демонстрации используем симуляцию данных
                    # Пытаемся получить реальные сообщения через Telethon
                    try:
                        from .telegram_reader import get_telegram_reader
                        real_reader = await get_telegram_reader()
                        if real_reader and real_reader.initialized:
                            messages = await real_reader.get_channel_messages(
                                channel['username'], 
                                limit=10, 
                                hours_lookback=self.hours_lookback
                            )
                            logger.info(f"📡 Используем реальные данные из {channel['username']}")
                        else:
                            # Fallback на симуляцию
                            messages = await self.channel_reader.simulate_channel_messages(
                                channel['username'], 
                                count=5
                            )
                            logger.info(f"🧪 Используем тестовые данные для {channel['username']}")
                    except ImportError:
                        # Fallback на симуляцию если telegram_reader недоступен
                        messages = await self.channel_reader.simulate_channel_messages(
                            channel['username'], 
                            count=5
                        )
                        logger.info(f"🧪 Используем тестовые данные для {channel['username']} (fallback)")
                    
                    # Фильтруем новые сообщения
                    new_messages = []
                    for msg in messages:
                        msg['channel_id'] = channel['id']
                        msg['priority'] = channel['priority']
                        
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
            
            logger.info(f"📊 Собрано {len(all_messages)} новых сообщений из {channels_processed} каналов")
            
            return {
                "success": True,
                "messages": all_messages,
                "channels_processed": channels_processed,
                "total_messages": len(all_messages)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка сбора новостей: {e}")
            return {"success": False, "error": str(e)}
    
    async def filter_and_prioritize(self, messages: List[Dict]) -> List[Dict]:
        """5.3. Фильтрация и приоритизация сообщений"""
        try:
            logger.info(f"🔍 Фильтрация и приоритизация {len(messages)} сообщений...")
            
            if not messages:
                return []
            
            # Фильтрация по времени
            time_limit = datetime.now() - timedelta(hours=self.hours_lookback)
            time_filtered = [msg for msg in messages if msg['date'] >= time_limit]
            
            logger.info(f"⏰ После фильтрации по времени ({self.hours_lookback}ч): {len(time_filtered)} сообщений")
            
            # Фильтрация по содержанию (EdTech релевантность)
            edtech_keywords = [
                'образование', 'обучение', 'курс', 'студент', 'учебн', 'школ', 'университет',
                'edtech', 'онлайн', 'платформа', 'технологи', 'стартап', 'инвестиции',
                'ИИ', 'AI', 'VR', 'AR', 'цифров', 'digital', 'learning'
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
            # Учитываем: приоритет канала, релевантность, время
            def priority_score(msg):
                return (
                    msg['priority'] * 10 +  # Приоритет канала (0-100)
                    msg.get('relevance_score', 0) * 5 +  # Релевантность (0-50+)
                    min(msg['views'] or 0, 1000) / 100  # Популярность (0-10)
                )
            
            content_filtered.sort(key=priority_score, reverse=True)
            
            # Ограничиваем количество
            final_messages = content_filtered[:self.max_news_count]
            
            logger.info(f"📋 Финальная выборка: {len(final_messages)} сообщений (макс. {self.max_news_count})")
            
            return final_messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка фильтрации сообщений: {e}")
            return messages[:self.max_news_count]  # Fallback: берем первые N
    
    async def summarize_messages(self, messages: List[Dict]) -> List[Dict]:
        """5.4. Суммаризация сообщений через Claude API"""
        try:
            logger.info(f"🤖 Начинаем суммаризацию {len(messages)} сообщений...")
            
            if not messages:
                return []
            
            # Подготавливаем сообщения для батчевой обработки
            batch_messages = []
            for msg in messages:
                batch_messages.append({
                    'text': msg['text'],
                    'channel': msg['channel'],
                    'original_msg': msg  # Сохраняем оригинальные данные
                })
            
            # Запускаем батчевую суммаризацию
            summarized = await self.claude_summarizer.summarize_batch(
                batch_messages, 
                max_concurrent=3
            )
            
            # Обрабатываем результаты
            processed_messages = []
            successful_summaries = 0
            
            for result in summarized:
                original_msg = result['original_msg']
                
                # Создаем финальную структуру сообщения
                processed_msg = {
                    **original_msg,
                    'summary': result['summary'],
                    'summary_success': result['summary_success'],
                    'summary_quality': result.get('summary_quality', 0),
                    'processing_time': result.get('processing_time', 0),
                    'fallback_used': result.get('fallback_used', False)
                }
                
                processed_messages.append(processed_msg)
                
                if result['summary_success']:
                    successful_summaries += 1
            
            success_rate = successful_summaries / len(messages) * 100 if messages else 0
            avg_quality = sum(msg.get('summary_quality', 0) for msg in processed_messages) / len(processed_messages) if processed_messages else 0
            
            logger.info(f"✅ Суммаризация завершена: {successful_summaries}/{len(messages)} ({success_rate:.1f}%) успешно")
            logger.info(f"📊 Средняя оценка качества: {avg_quality:.1f}/10")
            
            return processed_messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка суммаризации: {e}")
            # Fallback: возвращаем сообщения с исходным текстом как summary
            for msg in messages:
                msg['summary'] = msg['text'][:100] + "..."
                msg['summary_success'] = False
                msg['fallback_used'] = True
            return messages
    
    def format_digest(self, messages: List[Dict]) -> str:
        """5.5. Форматирование дайджеста для публикации"""
        try:
            logger.info(f"📝 Форматирование дайджеста из {len(messages)} новостей...")
            
            if not messages:
                return "📰 Новостей EdTech за последние часы не найдено."
            
            # Заголовок дайджеста
            current_time = datetime.now()
            time_str = current_time.strftime("%d.%m.%Y %H:%M")
            
            header = f"""📰 **EdTech Дайджест** | {time_str}
            
🔍 {len(messages)} главных новостей образовательных технологий:
"""
            
            # Форматируем каждую новость
            news_items = []
            for i, msg in enumerate(messages, 1):
                # Определяем иконку по приоритету канала
                if msg.get('priority', 0) >= 8:
                    icon = "🔥"  # Высокий приоритет
                elif msg.get('priority', 0) >= 5:
                    icon = "⭐"  # Средний приоритет
                else:
                    icon = "📌"  # Обычный приоритет
                
                # Форматируем новость
                summary = msg.get('summary', msg['text'][:100] + "...")
                channel_name = msg['channel'].replace('@', '')
                
                # Добавляем индикаторы качества
                quality_indicator = ""
                if msg.get('summary_success', False):
                    quality = msg.get('summary_quality', 0)
                    if quality >= 9:
                        quality_indicator = " ✨"  # Высокое качество
                    elif quality < 6:
                        quality_indicator = " 📝"  # Среднее качество
                
                news_item = f"{icon} **{i}.** {summary}{quality_indicator}\n└ [{channel_name}]({msg.get('link', '#')})"
                
                if msg.get('fallback_used'):
                    news_item += " 🔄"  # Индикатор fallback
                
                news_items.append(news_item)
            
            # Собираем итоговый дайджест
            digest = header + "\n\n".join(news_items)
            
            # Добавляем footer
            footer = f"""
            
---
🤖 Автоматический дайджест | Следующий выпуск через {self.hours_lookback} часов
💬 [Обратная связь](https://t.me/vestnik_edtech_bot)"""
            
            digest += footer
            
            # Проверяем длину (Telegram лимит ~4096 символов)
            if len(digest) > 4000:
                logger.warning("⚠️ Дайджест слишком длинный, сокращаем...")
                # Сокращаем количество новостей
                short_messages = messages[:min(8, len(messages))]
                return self.format_digest(short_messages)
            
            logger.info(f"📄 Дайджест сформирован: {len(digest)} символов, {len(messages)} новостей")
            return digest
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования дайджеста: {e}")
            return f"❌ Ошибка формирования дайджеста: {str(e)}"
    
    async def validate_and_publish(self, digest: str, messages: List[Dict]) -> Dict[str, Any]:
        """5.6. Валидация и публикация дайджеста"""
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
                # Не блокируем публикацию, но логируем проблемы
            
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
        """5.7. Полный цикл сбора, обработки и публикации новостей"""
        start_time = datetime.now()
        logger.info(f"🚀 Запуск полного цикла сбора новостей в {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Инициализация компонентов
            if not await self.initialize():
                raise Exception("Ошибка инициализации")
            
            # 5.2. Сбор новостей
            collection_result = await self.collect_news()
            if not collection_result["success"]:
                raise Exception(f"Ошибка сбора: {collection_result['error']}")
            
            messages = collection_result["messages"]
            channels_processed = collection_result["channels_processed"]
            
            # 5.3. Фильтрация и приоритизация
            filtered_messages = await self.filter_and_prioritize(messages)
            
            # 5.4. Суммаризация
            summarized_messages = await self.summarize_messages(filtered_messages)
            
            # 5.5. Форматирование
            digest = self.format_digest(summarized_messages)
            
            # 5.6. Валидация и публикация
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
            logger.error(f"❌ Ошибка полного цикла: {e}")
            
            # Обновляем лог об ошибке
            self._update_run_log(
                status="failed",
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
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