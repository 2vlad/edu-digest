#!/usr/bin/env python3
"""
Тест с добавлением реальных каналов для проверки работы
"""

import asyncio
import sys
sys.path.append('src')

from src.database import ChannelsDB

async def setup_test_channels():
    """Добавляем популярные EdTech каналы для теста"""
    
    test_channels = [
        ("@edtexno", "EdTexno", 10),
        ("@habr_career", "Карьера Хабр", 8),
        ("@te_st_channel", "Тестовый канал", 5),
    ]
    
    print("📡 Настройка тестовых каналов...")
    
    for username, display_name, priority in test_channels:
        try:
            # Проверяем, есть ли уже такой канал
            existing_channels = ChannelsDB.get_active_channels()
            exists = any(ch['username'] == username for ch in existing_channels)
            
            if not exists:
                channel_id = ChannelsDB.add_channel(username, display_name, priority)
                print(f"➕ Добавлен канал: {display_name} ({username}) - ID: {channel_id}")
            else:
                print(f"✅ Канал уже существует: {display_name} ({username})")
                
        except Exception as e:
            print(f"❌ Ошибка добавления канала {username}: {e}")
    
    # Показываем финальный список каналов
    channels = ChannelsDB.get_active_channels()
    print(f"\n📊 Всего активных каналов: {len(channels)}")
    for ch in channels:
        print(f"   - {ch['display_name']} ({ch['username']}) - приоритет: {ch['priority']}")

async def test_news_collection_with_channels():
    """Основной тест с каналами"""
    
    # Настраиваем каналы
    await setup_test_channels()
    
    # Импортируем NewsCollector
    from src.news_collector import NewsCollector
    
    print("\n🚀 Запуск сбора новостей...")
    
    collector = NewsCollector()
    await collector.initialize()
    
    # Запускаем полный цикл
    result = await collector.run_full_cycle()
    
    print(f"\n📊 Финальный результат:")
    print(f"   - Успех: {result.get('success', False)}")
    print(f"   - Обработано каналов: {result.get('channels_processed', 0)}")
    print(f"   - Сообщений собрано: {result.get('messages_collected', 0)}")
    print(f"   - Опубликовано новостей: {result.get('news_published', 0)}")
    
    if result.get('error'):
        print(f"   - Ошибка: {result['error']}")
    
    return result.get('success', False)

if __name__ == "__main__":
    success = asyncio.run(test_news_collection_with_channels())
    
    if success:
        print("\n✅ Все тесты прошли успешно!")
        print("🚀 Можно деплоить на Railway!")
    else:
        print("\n❌ Есть проблемы, нужно исправить перед деплоем")
        sys.exit(1)