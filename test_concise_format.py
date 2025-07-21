#!/usr/bin/env python3
"""
Тест лаконичного формата дайджеста
"""

import sys
sys.path.append('src')

from src.news_collector import NewsCollector
from src.database import ChannelsDB
import asyncio

async def test_concise_format():
    """Тест нового лаконичного формата"""
    
    print("🧪 Тестируем лаконичный формат дайджеста...")
    
    # Создаем тестовые сообщения
    test_messages = [
        {
            'id': 2001,
            'text': '🚀 Яндекс запустил новую платформу для обучения программированию с ИИ-ассистентом. Сервис использует GPT-4 для персонализированного обучения и доступен бесплатно для студентов российских вузов.',
            'channel': '@edtexno',
            'link': 'https://t.me/edtexno/2001',
            'summary': 'Яндекс запустил платформу обучения программированию с GPT-4',
            'priority': 10
        },
        {
            'id': 2002, 
            'text': '📚 Mail.ru Group объявила о создании образовательной экосистемы на базе VK. Планируется интеграция онлайн-курсов, вебинаров и интерактивных заданий прямо в социальной сети.',
            'channel': '@te_st_channel',
            'link': 'https://t.me/te_st_channel/2002',
            'summary': 'VK запускает образовательную экосистему с интегрированными курсами',
            'priority': 5
        },
        {
            'id': 2003,
            'text': '🎯 Сбер представил обновленную платформу Сбер Университет с технологиями виртуальной реальности. Студенты смогут изучать сложные предметы в иммерсивной среде.',
            'channel': '@vc_edtech',  
            'link': 'https://t.me/vc_edtech/2003',
            'summary': 'Сбер добавил VR-технологии в образовательную платформу',
            'priority': 10
        },
        {
            'id': 2004,
            'text': '💡 Российская EdTech компания MAXIMUM Education привлекла $15 млн инвестиций для расширения AI-платформы подготовки к ЕГЭ и международным экзаменам.',
            'channel': '@habr_career',
            'link': 'https://t.me/habr_career/2004', 
            'summary': 'MAXIMUM Education привлекла $15M для AI-платформы подготовки к ЕГЭ',
            'priority': 8
        },
        {
            'id': 2005,
            'text': '🌐 Нетология представила новый формат обучения с использованием нейросетей для автоматической проверки домашних заданий по программированию.',
            'channel': '@edcrunch',
            'link': 'https://t.me/edcrunch/2005',
            'summary': 'Нетология внедрила ИИ для проверки заданий по программированию',
            'priority': 7
        }
    ]
    
    # Создаем экземпляр NewsCollector
    collector = NewsCollector()
    
    # Форматируем дайджест
    digest = collector.format_digest(test_messages)
    
    print("\n" + "="*60)
    print("📄 РЕЗУЛЬТАТ - ЛАКОНИЧНЫЙ ДАЙДЖЕСТ:")
    print("="*60)
    print(digest)
    print("="*60)
    
    print(f"\n📊 Статистика:")
    print(f"   - Длина: {len(digest)} символов")
    print(f"   - Новостей: {len(test_messages)}")
    print(f"   - Строк: {digest.count(chr(10)) + 1}")

if __name__ == "__main__":
    asyncio.run(test_concise_format())