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
import pytz

# Добавляем путь к src модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

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
    """Получаем время запуска из настроек (московское время)"""
    try:
        from src.database import SettingsDB
        digest_times = SettingsDB.get_setting('digest_times', '12:00,18:00')
        times = [t.strip() for t in digest_times.split(',') if t.strip()]
        logger.info(f"📅 Время публикации из настроек (MSK): {times}")
        return times
    except Exception as e:
        logger.error(f"❌ Ошибка получения времени из настроек: {e}")
        # Fallback к значениям по умолчанию
        return ['12:00', '18:00']

def schedule_moscow_time(time_str: str, job_func):
    """Планирование задания на московское время"""
    try:
        # Парсим время
        hour, minute = map(int, time_str.split(':'))
        
        def moscow_job():
            """Обертка для выполнения задания с проверкой московского времени"""
            moscow_now = datetime.now(MOSCOW_TZ)
            current_hour = moscow_now.hour
            current_minute = moscow_now.minute
            
            # Проверяем что сейчас нужное время в Москве (с допуском в 1 минуту)
            if abs(current_hour - hour) == 0 and abs(current_minute - minute) <= 1:
                logger.info(f"🕐 Запуск задания в московское время: {moscow_now.strftime('%H:%M MSK')}")
                job_func()
            else:
                logger.debug(f"⏰ Пропуск: текущее время MSK {current_hour:02d}:{current_minute:02d}, ожидаем {hour:02d}:{minute:02d}")
        
        return moscow_job
    except Exception as e:
        logger.error(f"❌ Ошибка создания московского расписания для {time_str}: {e}")
        return job_func

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
    """Настройка расписания (все времена в московском часовом поясе)"""
    logger.info("⏰ Настройка расписания автоматических запусков (московское время)...")
    
    # Очищаем предыдущие задания
    schedule.clear()
    
    # Настраиваем почасовой сбор новостей (накопление)
    schedule.every().hour.do(run_news_collection)
    logger.info("📅 Настроен почасовой сбор новостей")
    
    # Получаем время публикации из настроек (московское время)
    times = get_schedule_times()
    
    # Настраиваем публикацию для каждого времени в московском часовом поясе
    for time_str in times:
        try:
            # Проверяем формат времени
            datetime.strptime(time_str, '%H:%M')
            
            # Создаем обертку для московского времени
            moscow_job = schedule_moscow_time(time_str, publish_accumulated_news)
            
            # Планируем проверку каждую минуту (schedule будет проверять московское время)
            schedule.every().minute.do(moscow_job)
            logger.info(f"📅 Настроена публикация дайджеста в {time_str} MSK каждый день")
            
        except ValueError:
            logger.error(f"❌ Неверный формат времени: {time_str}. Ожидается HH:MM")
    
    # Если не удалось настроить публикацию, используем значения по умолчанию
    if not times or len(times) == 0:
        logger.warning("⚠️ Не удалось настроить публикацию! Используем значения по умолчанию")
        for default_time in ["12:00", "18:00"]:
            moscow_job = schedule_moscow_time(default_time, publish_accumulated_news)
            schedule.every().minute.do(moscow_job)
        logger.info("📅 Настроена публикация по умолчанию: 12:00 и 18:00 MSK")
    
    logger.info(f"✅ Настроено {len(schedule.jobs)} автоматических заданий в московском времени")
    
    # Показываем текущее время
    moscow_now = datetime.now(MOSCOW_TZ)
    logger.info(f"🕐 Текущее московское время: {moscow_now.strftime('%Y-%m-%d %H:%M:%S MSK')}")

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
    
    # Показываем время в московском часовом поясе
    moscow_now = datetime.now(MOSCOW_TZ)
    logger.info(f"📅 Время запуска (MSK): {moscow_now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🌍 Часовой пояс: Europe/Moscow (UTC+3)")
    
    # Также показываем локальное время сервера для сравнения
    local_now = datetime.now()
    logger.info(f"🖥️ Локальное время сервера: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
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