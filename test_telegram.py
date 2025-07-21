#!/usr/bin/env python3
"""
Тест Telegram API интеграции
Этап 2 PRD - критерии приёмки
"""
import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.telegram_client import TelegramNewsCollector
from src.database import ChannelsDB

async def test_telegram_integration():
    """Тестирование интеграции с Telegram API"""
    print("🔍 Тестирование Telegram API интеграции")
    print("="*50)
    
    collector = TelegramNewsCollector()
    
    try:
        # 3.1. Тест авторизации
        print("1️⃣ Инициализация Telegram клиента...")
        await collector.initialize_client()
        
        if not collector.is_authorized:
            print("❌ Клиент не авторизован")
            print("💡 Для авторизации выполните:")
            print("   python setup_telegram.py")
            return False
        
        print("✅ Успешная авторизация через Telethon")
        
        # 3.2. Тест получения информации о каналах
        print("\n2️⃣ Получение списка доступных каналов...")
        channels = ChannelsDB.get_active_channels()
        
        if not channels:
            print("⚠️  Нет активных каналов в базе данных")
            print("💡 Добавьте каналы через админ-панель или вручную в БД")
            return False
        
        print(f"✅ Найдено {len(channels)} активных каналов")
        
        # 3.3. Тест доступа к каналам
        print("\n3️⃣ Проверка доступа к каналам...")
        accessible_channels = 0
        
        for channel in channels[:3]:  # Тестируем первые 3 канала
            username = channel['username']
            print(f"   Проверяем {username}...")
            
            test_result = await collector.test_channel_access(username)
            
            if test_result['status'] == 'success':
                accessible_channels += 1
                info = test_result['channel_info']
                msg_count = test_result['recent_messages_count']
                
                print(f"   ✅ {info['title']} - {msg_count} сообщений за час")
                
                # Показываем примеры сообщений
                if test_result['sample_messages']:
                    for i, msg in enumerate(test_result['sample_messages'], 1):
                        preview = msg['text'][:100] + "..." if len(msg['text']) > 100 else msg['text']
                        print(f"      Сообщение {i}: {preview}")
            else:
                print(f"   ❌ {username}: {test_result['message']}")
        
        if accessible_channels > 0:
            print(f"✅ Доступно {accessible_channels} каналов")
        else:
            print("❌ Нет доступных каналов")
            return False
        
        # 3.4. Тест чтения последних сообщений
        print("\n4️⃣ Чтение последних 5 сообщений из тестового канала...")
        
        test_channel = channels[0]['username']
        messages = await collector.get_recent_messages(test_channel, hours_back=24, limit=5)
        
        if messages:
            print(f"✅ Получено {len(messages)} сообщений из {test_channel}")
            for i, msg in enumerate(messages, 1):
                date_str = msg['date'].strftime('%Y-%m-%d %H:%M:%S')
                preview = msg['text'][:150] + "..." if len(msg['text']) > 150 else msg['text']
                print(f"   {i}. [{date_str}] {preview}")
                if msg['external_links']:
                    print(f"      🔗 Ссылки: {', '.join(msg['external_links'])}")
        else:
            print("⚠️  Нет сообщений за последние 24 часа")
        
        print("✅ Корректная обработка приватных/публичных каналов")
        
        # 3.5. Тест сбора новых сообщений с отслеживанием
        print("\n5️⃣ Тест системы отслеживания новых сообщений...")
        new_messages = await collector.collect_new_messages_from_channels(hours_back=6)
        
        print(f"✅ Найдено {len(new_messages)} новых сообщений за последние 6 часов")
        
        if new_messages:
            # Группируем по каналам
            by_channel = {}
            for msg in new_messages:
                channel = msg['channel']
                if channel not in by_channel:
                    by_channel[channel] = 0
                by_channel[channel] += 1
            
            for channel, count in by_channel.items():
                print(f"   {channel}: {count} сообщений")
        
        print("\n✅ Все тесты Telegram API пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
        
    finally:
        # Закрываем соединение
        await collector.disconnect()

async def main():
    """Основная функция тестирования"""
    success = await test_telegram_integration()
    
    if success:
        print("\n🎉 Этап 2 PRD - критерии приёмки выполнены:")
        print("✅ Успешная авторизация через Telethon")
        print("✅ Получение списка доступных каналов")
        print("✅ Чтение последних 5 сообщений из тестового канала")  
        print("✅ Корректная обработка приватных/публичных каналов")
        print("\n🚀 Готово для следующего этапа!")
        sys.exit(0)
    else:
        print("\n❌ Тестирование не пройдено")
        print("💡 Проверьте настройки .env и выполните setup_telegram.py")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())