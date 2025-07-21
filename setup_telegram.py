#!/usr/bin/env python3
"""
Скрипт первичной настройки Telegram авторизации
Запускается один раз для авторизации клиента
"""
import asyncio
import sys
import os
import getpass

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.telegram_client import TelegramNewsCollector

async def setup_telegram_auth():
    """Первичная настройка Telegram авторизации"""
    print("📱 Настройка авторизации Telegram")
    print("="*40)
    print("Этот скрипт нужно запустить один раз для авторизации клиента")
    print("После авторизации создастся сессионный файл для автоматического входа")
    print()
    
    collector = TelegramNewsCollector()
    
    try:
        # Инициализируем клиент
        await collector.initialize_client()
        
        if collector.is_authorized:
            print("✅ Клиент уже авторизован!")
            me = await collector.client.get_me()
            print(f"   Пользователь: {me.first_name} (@{me.username})")
            return True
        
        print("🔑 Требуется авторизация...")
        
        # Запрашиваем номер телефона
        phone = input("Введите номер телефона (с кодом страны, например +79001234567): ")
        
        # Отправляем код
        if not await collector.authorize_with_phone(phone):
            print("❌ Ошибка отправки кода")
            return False
        
        # Запрашиваем код подтверждения
        code = input("Введите код из SMS: ")
        
        result = await collector.verify_code(phone, code)
        
        if result is True:
            print("✅ Авторизация успешна!")
            me = await collector.client.get_me()
            print(f"   Добро пожаловать, {me.first_name}!")
            return True
            
        elif result == "2fa_required":
            print("🔐 Требуется пароль двухфакторной аутентификации")
            password = getpass.getpass("Введите пароль: ")
            
            if await collector.sign_in_with_password(password):
                print("✅ Авторизация с 2FA успешна!")
                return True
            else:
                print("❌ Неверный пароль 2FA")
                return False
        else:
            print("❌ Ошибка авторизации")
            return False
    
    except KeyboardInterrupt:
        print("\n⚠️  Авторизация отменена пользователем")
        return False
    except Exception as e:
        print(f"❌ Ошибка настройки: {e}")
        return False
    finally:
        await collector.disconnect()

async def main():
    """Основная функция"""
    print("Убедитесь, что в .env файле указаны:")
    print("- TELEGRAM_API_ID")
    print("- TELEGRAM_API_HASH")
    print()
    
    proceed = input("Продолжить настройку? (y/N): ")
    if proceed.lower() not in ['y', 'yes', 'да']:
        print("Настройка отменена")
        return
    
    success = await setup_telegram_auth()
    
    if success:
        print("\n🎉 Telegram авторизация настроена!")
        print("📄 Создан файл сессии: edu_digest_bot.session")
        print("🔄 Теперь можно запустить: python test_telegram.py")
    else:
        print("\n❌ Не удалось настроить авторизацию")
        print("💡 Проверьте правильность введённых данных")

if __name__ == "__main__":
    asyncio.run(main())