#!/usr/bin/env python3
"""
Простой тест подключения к Telegram API для диагностики
Проверяет можем ли мы подключиться к реальным каналам
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append('src')

async def test_telegram_connection():
    """Тест подключения к Telegram API"""
    print("🧪 Тест подключения к Telegram API")
    print("=" * 50)
    
    # Проверяем переменные окружения
    from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN
    
    print(f"🔍 Environment Variables Check:")
    print(f"   TELEGRAM_API_ID: {'✅ Set' if TELEGRAM_API_ID else '❌ Missing'}")
    print(f"   TELEGRAM_API_HASH: {'✅ Set' if TELEGRAM_API_HASH else '❌ Missing'}")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ Set' if TELEGRAM_BOT_TOKEN else '❌ Missing'}")
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("\n❌ CRITICAL ERROR: Missing Telegram API credentials")
        print("💡 Required variables:")
        print("   - TELEGRAM_API_ID (get from https://my.telegram.org/auth)")
        print("   - TELEGRAM_API_HASH (get from https://my.telegram.org/auth)")
        print("   - TELEGRAM_BOT_TOKEN (get from @BotFather)")
        return False
    
    print(f"\n🔗 Testing Telegram connection...")
    
    try:
        # Тест через Telethon (User API)
        print("🔵 Testing Telethon User API...")
        from telegram_reader import get_telegram_reader
        
        reader = await get_telegram_reader()
        if reader and reader.initialized:
            print("✅ Telethon User API connection successful")
            
            # Тест чтения канала
            print("📺 Testing channel reading...")
            test_channel = "@edtexno"  # Популярный EdTech канал
            
            try:
                messages = await reader.get_channel_messages(test_channel, limit=3, hours_lookback=24)
                if messages:
                    print(f"✅ Successfully read {len(messages)} messages from {test_channel}")
                    for i, msg in enumerate(messages[:2]):  # Показываем первые 2
                        print(f"   📄 Message {i+1}: {msg.get('text', 'No text')[:100]}...")
                else:
                    print(f"⚠️ No messages found in {test_channel} (last 24 hours)")
                    
            except Exception as channel_error:
                print(f"❌ Error reading channel {test_channel}: {channel_error}")
                
        else:
            print("❌ Telethon User API connection failed")
            
    except Exception as telethon_error:
        print(f"❌ Telethon error: {telethon_error}")
    
    try:
        # Тест через python-telegram-bot (Bot API)
        print("\n🔵 Testing Bot API...")
        from telegram_publisher import TelegramPublisher
        
        publisher = TelegramPublisher()
        if await publisher.test_connection():
            print("✅ Bot API connection successful")
        else:
            print("❌ Bot API connection failed")
            
    except Exception as bot_error:
        print(f"❌ Bot API error: {bot_error}")
    
    print("\n" + "=" * 50)
    print("🔧 RECOMMENDATIONS:")
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("1. 🔑 Add missing Telegram API credentials to Railway")
        print("   - Go to https://my.telegram.org/auth")
        print("   - Create an application to get API_ID and API_HASH")
        print("   - Add them to Railway Environment Variables")
        
    print("2. 📱 Ensure the Telegram account has access to target channels")
    print("3. 🌐 Check network connectivity to Telegram servers")
    print("4. 🔄 Redeploy Railway service after adding variables")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())