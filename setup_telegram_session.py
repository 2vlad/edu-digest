#!/usr/bin/env python3
"""
Скрипт для настройки Telegram сессии
Запускается один раз для создания файла .session
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

# Загружаем переменные окружения
load_dotenv()

def main():
    """Основная функция настройки сессии"""
    print("🚀 Настройка Telegram сессии для EdTech News Digest Bot")
    print("=" * 60)
    
    # Получаем переменные окружения
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("❌ Ошибка: Не найдены TELEGRAM_API_ID или TELEGRAM_API_HASH в .env файле")
        print("💡 Получите их на https://my.telegram.org/auth")
        return False
    
    print(f"✅ API ID: {api_id}")
    print(f"✅ API Hash: {api_hash[:10]}...")
    print()
    
    async def create_session():
        """Создание сессии"""
        session_file = 'telegram_session'
        
        # Создаем клиент
        client = TelegramClient(session_file, int(api_id), api_hash)
        
        try:
            print("🔗 Подключение к Telegram...")
            await client.start()
            
            # Проверяем авторизацию
            me = await client.get_me()
            print(f"✅ Успешно аутентифицированы как: {me.first_name}")
            if me.username:
                print(f"   Username: @{me.username}")
            print(f"   Phone: {me.phone}")
            
            # Тестируем доступ к каналу
            try:
                channel = await client.get_entity('@habr_career')
                print(f"✅ Тестовый доступ к каналу: {channel.title}")
            except Exception as e:
                print(f"⚠️ Не удалось получить доступ к тестовому каналу: {e}")
            
            print(f"✅ Сессия сохранена в файл: {session_file}.session")
            
            await client.disconnect()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания сессии: {e}")
            await client.disconnect()
            return False
    
    # Запускаем создание сессии
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(create_session())
        if success:
            print()
            print("🎉 Настройка завершена успешно!")
            print("💡 Теперь можно запускать сбор новостей")
            return True
        else:
            print()
            print("❌ Настройка не удалась")
            return False
    finally:
        loop.close()

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)