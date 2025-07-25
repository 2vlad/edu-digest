#!/usr/bin/env python3
"""
Скрипт для создания Telegram сессии для Railway
Запустить локально, скопировать файл сессии
"""

import asyncio
from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')

async def create_session():
    print("🔧 Создание сессии для Railway...")
    
    client = TelegramClient('railway_session', API_ID, API_HASH)
    
    await client.start()
    print("✅ Сессия создана!")
    
    me = await client.get_me()
    print(f"👤 Вошли как: {me.first_name} (@{me.username})")
    
    await client.disconnect()
    print("🎉 Готово! Файл 'railway_session.session' создан")
    print("📂 Скопируйте этот файл в Railway через git или другим способом")

if __name__ == '__main__':
    asyncio.run(create_session()) 