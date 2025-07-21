#!/usr/bin/env python3
"""
Локальный тест для проверки сбора новостей
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Добавляем путь к src
sys.path.append('src')

async def test_news_collection():
    """Тест сбора новостей локально"""
    print("🚀 Запуск теста сбора новостей...")
    
    try:
        # Импортируем NewsCollector
        from src.news_collector import NewsCollector
        print("✅ NewsCollector импортирован успешно")
        
        # Проверяем переменные окружения
        required_env_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
            return False
        
        print("✅ Все переменные окружения найдены")
        
        # Создаем и инициализируем NewsCollector
        collector = NewsCollector()
        print("✅ NewsCollector создан")
        
        # Инициализируем компоненты
        await collector.initialize()
        print("✅ NewsCollector инициализирован")
        
        # Проверяем количество каналов
        from src.database import ChannelsDB
        channels = ChannelsDB.get_active_channels()
        print(f"📡 Найдено активных каналов: {len(channels)}")
        
        if len(channels) == 0:
            print("⚠️ Нет активных каналов для тестирования")
            # Добавим тестовый канал
            channel_id = ChannelsDB.add_channel("@edtexno", "EdTech News Test", priority=5)
            print(f"➕ Добавлен тестовый канал: @edtexno (ID: {channel_id})")
            channels = ChannelsDB.get_active_channels()
        
        # Запускаем полный цикл
        print("🔄 Запуск полного цикла сбора новостей...")
        result = await collector.run_full_cycle()
        
        print(f"📊 Результат выполнения:")
        print(f"   - Успех: {result.get('success', False)}")
        print(f"   - Обработано каналов: {result.get('channels_processed', 0)}")
        print(f"   - Сообщений собрано: {result.get('messages_collected', 0)}")
        print(f"   - Опубликовано новостей: {result.get('news_published', 0)}")
        
        if not result.get('success'):
            print(f"❌ Ошибка: {result.get('error', 'Unknown')}")
        
        return result.get('success', False)
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO)
    
    print(f"🕒 Начало теста: {datetime.now()}")
    
    # Запускаем тест
    success = asyncio.run(test_news_collection())
    
    print(f"🕒 Конец теста: {datetime.now()}")
    
    if success:
        print("✅ Тест завершен успешно!")
        sys.exit(0)
    else:
        print("❌ Тест завершен с ошибками!")
        sys.exit(1)