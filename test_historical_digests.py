#!/usr/bin/env python3
"""
Тестирование генератора ретроспективных дайджестов (без публикации)
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta, time, date

# Импортируем наши модули
sys.path.append('/Users/tovlad01/Dev/edu-digest')
from generate_historical_digests import HistoricalDigestGenerator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_historical_digests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def test_single_digest():
    """Тест создания одного дайджеста без публикации"""
    
    logger.info("🧪 Тестирование создания одного исторического дайджеста...")
    
    generator = HistoricalDigestGenerator()
    
    try:
        await generator.initialize()
        
        # Тестируем на 24 июля, утренний дайджест
        test_date = date(2025, 7, 24)
        
        result = await generator.create_historical_digest(
            target_date=test_date,
            digest_type="Утренний",
            start_hour=6,
            end_hour=12,
            publish=False  # НЕ публикуем, только тестируем
        )
        
        if result["success"]:
            logger.info("✅ Тест успешен!")
            logger.info(f"📊 Найдено сообщений: {result['messages_count']}")
            logger.info("📰 Сгенерированный дайджест:")
            logger.info("=" * 60)
            print(result["digest_text"])
            logger.info("=" * 60)
        else:
            logger.error(f"❌ Тест не прошел: {result['reason']}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    try:
        asyncio.run(test_single_digest())
    except KeyboardInterrupt:
        logger.info("⏹️ Тест прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")