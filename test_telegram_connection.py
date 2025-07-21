#!/usr/bin/env python3
"""
Простой тест подключения к Telegram API без авторизации
Проверяет корректность API ключей и базовую работу Telethon
"""
import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from telethon import TelegramClient
from src.config import TELEGRAM_API_ID, TELEGRAM_API_HASH

async def test_api_connection():
    """Тест базового подключения к Telegram API"""
    print("🔌 Тестирование подключения к Telegram API")
    print("="*45)
    
    # Проверяем наличие API ключей
    print("1️⃣ Проверка конфигурации...")
    
    if not TELEGRAM_API_ID or TELEGRAM_API_ID == "your_telegram_api_id":
        print("❌ TELEGRAM_API_ID не настроен в .env")
        return False
        
    if not TELEGRAM_API_HASH or TELEGRAM_API_HASH == "your_telegram_api_hash":
        print("❌ TELEGRAM_API_HASH не настроен в .env")
        return False
    
    print(f"✅ API ID: {TELEGRAM_API_ID}")
    print(f"✅ API Hash: {TELEGRAM_API_HASH[:8]}...")
    
    # Тестируем создание клиента
    print("\n2️⃣ Создание Telegram клиента...")
    try:
        client = TelegramClient("test_session", TELEGRAM_API_ID, TELEGRAM_API_HASH)
        print("✅ Клиент создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        return False
    
    # Тестируем подключение (без авторизации)
    print("\n3️⃣ Тест подключения к серверам Telegram...")
    try:
        await client.connect()
        if client.is_connected():
            print("✅ Подключение к Telegram API установлено")
            connection_success = True
        else:
            print("❌ Не удалось подключиться")
            connection_success = False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        connection_success = False
    finally:
        if client.is_connected():
            await client.disconnect()
    
    # Проверяем статус авторизации
    print("\n4️⃣ Проверка авторизации...")
    try:
        temp_client = TelegramClient("edu_digest_bot", TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await temp_client.connect()
        
        if await temp_client.is_user_authorized():
            print("✅ Пользователь уже авторизован")
            me = await temp_client.get_me()
            print(f"   Имя: {me.first_name}")
            if me.username:
                print(f"   Username: @{me.username}")
            authorized = True
        else:
            print("⚠️  Пользователь не авторизован")
            print("💡 Для авторизации создайте интерактивный скрипт или используйте другой метод")
            authorized = False
            
        await temp_client.disconnect()
        
    except Exception as e:
        print(f"⚠️  Не удалось проверить авторизацию: {e}")
        authorized = False
    
    # Итоговый результат
    print("\n📊 Результат тестирования:")
    if connection_success:
        print("✅ Подключение к Telegram API работает")
        if authorized:
            print("✅ Пользователь авторизован - готов к работе")
            return True
        else:
            print("⚠️  Требуется авторизация пользователя")
            print("💡 Создайте бота или авторизуйтесь как пользователь")
            return "auth_needed"
    else:
        print("❌ Проблемы с подключением к API")
        return False

async def main():
    """Основная функция"""
    result = await test_api_connection()
    
    print("\n🎯 Следующие шаги:")
    if result is True:
        print("🚀 API готов к работе! Можно запускать основной функционал")
    elif result == "auth_needed":
        print("📱 Настройте авторизацию через setup_telegram.py или используйте бота")
    else:
        print("🔧 Проверьте настройки API в .env файле")

if __name__ == "__main__":
    asyncio.run(main())