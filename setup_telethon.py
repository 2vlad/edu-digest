#!/usr/bin/env python3
"""
Одноразовый скрипт для настройки Telethon авторизации
"""

import asyncio
from telethon import TelegramClient
from src.config import TELEGRAM_API_ID, TELEGRAM_API_HASH

async def setup_telethon():
    """Настройка Telethon с интерактивной авторизацией"""
    
    client = TelegramClient('edu_digest_bot', int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
    
    print("🔐 Настройка Telethon для чтения каналов...")
    print("📱 Вам понадобится номер телефона и код из SMS")
    
    await client.start()
    
    # Проверяем авторизацию
    me = await client.get_me()
    if me:
        print(f"✅ Авторизация успешна: {me.first_name} ({me.username})")
        print(f"📱 Телефон: {me.phone}")
        print("💾 Сессия сохранена в файл edu_digest_bot.session")
        
        # Тестируем чтение канала
        print("\n🧪 Тестируем чтение канала @edtexno...")
        try:
            entity = await client.get_entity('@edtexno')
            print(f"📡 Канал найден: {entity.title}")
            
            messages_count = 0
            async for message in client.iter_messages(entity, limit=3):
                if message.text:
                    messages_count += 1
                    print(f"📄 Сообщение {messages_count}: {message.text[:100]}...")
            
            print(f"✅ Получено {messages_count} сообщений")
            
        except Exception as e:
            print(f"❌ Ошибка чтения канала: {e}")
    
    await client.disconnect()
    print("✅ Настройка завершена!")

if __name__ == "__main__":
    asyncio.run(setup_telethon())