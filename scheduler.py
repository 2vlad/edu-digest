#!/usr/bin/env python3
"""
Task 10: Планировщик автоматического запуска
Автоматический запуск сбора новостей в заданное время (12:00 и 18:00)
"""

import asyncio
import logging
import schedule
import time
import sys
import os
from datetime import datetime
from threading import Thread

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.news_collector import NewsCollector
from src.database import SettingsDB

# Настройка логирования
os.makedirs('logs', exist_ok=True)  # Создаем папку logs если не существует
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NewsScheduler:
    """Планировщик автоматического сбора новостей"""
    
    def __init__(self):
        self.is_running = False
        self.collector = None
        
    async def run_news_collection(self):
        """Выполнение сбора новостей"""
        try:
            logger.info("🚀 Начинаем запланированный сбор новостей...")
            
            # Создаем новый экземпляр коллектора для каждого запуска
            collector = NewsCollector()
            result = await collector.run_full_cycle()
            
            if result["success"]:
                logger.info("✅ Запланированный сбор новостей завершен успешно!")
                logger.info(f"📊 Обработано: {result['channels_processed']} каналов, {result['messages_collected']} сообщений")
                logger.info(f"📰 Опубликовано: {result['news_published']} новостей")
            else:
                logger.error(f"❌ Ошибка запланированного сбора новостей: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"💥 Критическая ошибка в запланированном сборе: {e}")
    
    def schedule_job(self):
        """Обертка для asyncio вызова из schedule"""
        try:
            # Запускаем асинхронную функцию в новом event loop
            asyncio.run(self.run_news_collection())
        except Exception as e:
            logger.error(f"Ошибка выполнения запланированной задачи: {e}")
    
    def setup_schedule(self):
        """Настройка расписания запусков"""
        try:
            # Получаем время из настроек базы данных
            digest_times = SettingsDB.get_setting('digest_times', '12:00,18:00')
            times = [t.strip() for t in digest_times.split(',')]
            
            logger.info(f"⏰ Настройка расписания для времени: {times}")
            
            # Очищаем существующие задачи
            schedule.clear()
            
            # Добавляем задачи для каждого времени
            for time_str in times:
                try:
                    # Валидация формата времени
                    datetime.strptime(time_str, '%H:%M')
                    schedule.every().day.at(time_str).do(self.schedule_job)
                    logger.info(f"✅ Добавлено расписание: {time_str}")
                except ValueError:
                    logger.warning(f"⚠️ Неверный формат времени: {time_str}, пропускаем")
            
            logger.info(f"📅 Всего настроено {len(schedule.jobs)} заданий")
            
        except Exception as e:
            logger.error(f"Ошибка настройки расписания: {e}")
            # Fallback расписание
            schedule.every().day.at("12:00").do(self.schedule_job)
            schedule.every().day.at("18:00").do(self.schedule_job)
            logger.info("🔄 Использовано fallback расписание: 12:00, 18:00")
    
    def run_scheduler(self):
        """Основной цикл планировщика"""
        logger.info("🎯 Запуск планировщика новостей...")
        
        # Настраиваем расписание
        self.setup_schedule()
        
        # Выводим информацию о следующих запусках
        if schedule.jobs:
            next_run = schedule.next_run()
            logger.info(f"⏳ Следующий запуск: {next_run}")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Проверяем задачи к выполнению
                schedule.run_pending()
                
                # Проверяем изменения в настройках каждые 10 минут
                now = datetime.now()
                if now.minute % 10 == 0 and now.second < 10:
                    self.setup_schedule()
                
                # Пауза между проверками
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки...")
        except Exception as e:
            logger.error(f"💥 Критическая ошибка планировщика: {e}")
        finally:
            self.is_running = False
            logger.info("🛑 Планировщик остановлен")
    
    def stop(self):
        """Остановка планировщика"""
        self.is_running = False

def run_scheduler_daemon():
    """Запуск планировщика в daemon режиме"""
    scheduler = NewsScheduler()
    
    def signal_handler(signum, frame):
        logger.info("Получен сигнал завершения")
        scheduler.stop()
        sys.exit(0)
    
    # Обработка сигналов завершения
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запуск планировщика
    scheduler.run_scheduler()

def test_immediate_run():
    """Тестовый запуск сбора новостей"""
    logger.info("🧪 Тестовый запуск сбора новостей...")
    scheduler = NewsScheduler()
    
    # Запускаем немедленно
    asyncio.run(scheduler.run_news_collection())

if __name__ == "__main__":
    print("EdTech News Digest - Планировщик")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Тестовый режим - запуск немедленно
        test_immediate_run()
    else:
        # Обычный режим - запуск планировщика
        run_scheduler_daemon()