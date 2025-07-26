#!/usr/bin/env python3
"""
Планировщик автоматических запусков EdTech News Digest
Запускает сбор новостей в заданное время каждый день
"""
import os
import sys
import asyncio
import logging
import schedule
import time
from datetime import datetime, timezone

# Добавляем путь к src модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Настройка логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_schedule_times():
    """Получаем время запуска из настроек"""
    try:
        from src.database import SettingsDB
        digest_times = SettingsDB.get_setting('digest_times', '12:00,18:00')
        times = [t.strip() for t in digest_times.split(',') if t.strip()]
        logger.info(f"📅 Время публикации из настроек: {times}")
        return times
    except Exception as e:
        logger.error(f"❌ Ошибка получения времени из настроек: {e}")
        # Fallback к значениям по умолчанию
        return ['12:00', '18:00']

def run_news_collection():
    """Запуск сбора новостей (накопление)"""
    logger.info("🚀 Запуск автоматического сбора новостей (накопление)...")
    
    try:
        # Импортируем функцию сбора
        from main import run_collect
        
        # Создаем новый event loop для асинхронного выполнения
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = datetime.now()
            result_code = loop.run_until_complete(run_collect())
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result_code == 0:
                logger.info(f"✅ Автоматический сбор завершен успешно за {duration:.2f}с")
            else:
                logger.error(f"❌ Автоматический сбор завершился с ошибкой (код: {result_code})")
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка автоматического сбора: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")

def publish_accumulated_news():
    """Публикация накопленного дайджеста"""
    logger.info("📤 Запуск публикации накопленного дайджеста...")
    
    try:
        from src.news_collector import NewsCollector
        
        # Создаем новый event loop для асинхронного выполнения
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = datetime.now()
            collector = NewsCollector()
            
            # Инициализация
            loop.run_until_complete(collector.initialize())
            
            # Публикация накопленного
            result = loop.run_until_complete(collector.publish_accumulated_digest())
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result['success']:
                logger.info(f"✅ Публикация завершена успешно за {duration:.2f}с")
                logger.info(f"📰 Опубликовано новостей: {result.get('news_count', 0)}")
            else:
                logger.error(f"❌ Публикация завершилась с ошибкой: {result.get('error', 'Unknown')}")
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка публикации: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")

def setup_schedule():
    """Настройка расписания"""
    logger.info("⏰ Настройка расписания автоматических запусков...")
    
    # Очищаем предыдущие задания
    schedule.clear()
    
    # Настраиваем почасовой сбор новостей (накопление)
    schedule.every().hour.do(run_news_collection)
    logger.info("📅 Настроен почасовой сбор новостей")
    
    # Получаем время публикации из настроек
    times = get_schedule_times()
    
    # Настраиваем публикацию для каждого времени
    for time_str in times:
        try:
            # Проверяем формат времени
            datetime.strptime(time_str, '%H:%M')
            
            # Добавляем задание публикации
            schedule.every().day.at(time_str).do(publish_accumulated_news)
            logger.info(f"📅 Настроена публикация дайджеста в {time_str} каждый день")
            
        except ValueError:
            logger.error(f"❌ Неверный формат времени: {time_str}. Ожидается HH:MM")
    
    # Если не удалось настроить публикацию, используем значения по умолчанию
    publication_jobs = [job for job in schedule.jobs if job.job_func == publish_accumulated_news]
    if not publication_jobs:
        logger.warning("⚠️ Не удалось настроить публикацию! Используем значения по умолчанию")
        schedule.every().day.at("12:00").do(publish_accumulated_news)
        schedule.every().day.at("18:00").do(publish_accumulated_news)
        logger.info("📅 Настроена публикация по умолчанию: 12:00 и 18:00")
    
    logger.info(f"✅ Настроено {len(schedule.jobs)} автоматических заданий:"
                f" {len([j for j in schedule.jobs if j.job_func == run_news_collection])} сбор,"
                f" {len([j for j in schedule.jobs if j.job_func == publish_accumulated_news])} публикация")

def log_next_runs():
    """Логируем информацию о следующих запусках"""
    if schedule.jobs:
        logger.info("📋 Следующие запланированные запуски:")
        for job in schedule.jobs:
            next_run = job.next_run
            if next_run:
                # Форматируем время с учетом часового пояса
                formatted_time = next_run.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"   ⏰ {formatted_time}")
    else:
        logger.warning("⚠️ Нет запланированных заданий")

def main():
    """Основная функция планировщика"""
    logger.info("🤖 Запуск планировщика EdTech News Digest...")
    logger.info("=" * 60)
    logger.info(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🌍 Часовой пояс: {datetime.now().astimezone().tzinfo}")
    logger.info("=" * 60)
    
    # Настраиваем расписание
    setup_schedule()
    log_next_runs()
    
    logger.info("🔄 Планировщик запущен. Ожидание заданий...")
    
    try:
        while True:
            # Проверяем и выполняем запланированные задания
            schedule.run_pending()
            
            # Спим 60 секунд между проверками
            time.sleep(60)
            
            # Каждые 6 часов обновляем расписание (на случай изменения настроек)
            current_time = datetime.now()
            if current_time.minute == 0 and current_time.hour % 6 == 0:
                logger.info("🔄 Обновление расписания...")
                setup_schedule()
                log_next_runs()
                
    except KeyboardInterrupt:
        logger.info("⏹️ Планировщик остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка планировщика: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()