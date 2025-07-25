#!/usr/bin/env python3
"""
Конвертирует файл сессии Telegram в base64 для Railway
"""

import base64
import os

def convert_session_to_base64():
    """Конвертирует railway_session.session в base64"""
    
    session_file = 'railway_session.session'
    
    if not os.path.exists(session_file):
        print(f"❌ Файл {session_file} не найден!")
        print("💡 Сначала запустите create_session_for_railway.py")
        return
    
    print(f"📄 Читаем файл {session_file}...")
    
    try:
        with open(session_file, 'rb') as f:
            session_data = f.read()
        
        # Кодируем в base64
        encoded = base64.b64encode(session_data).decode('utf-8')
        
        print("✅ Файл успешно закодирован!")
        print()
        print("📋 Добавьте эту переменную в Railway Environment Variables:")
        print("=" * 60)
        print(f"TELEGRAM_SESSION_BASE64={encoded}")
        print("=" * 60)
        print()
        print("💡 Инструкция:")
        print("1. Откройте ваш проект в Railway")
        print("2. Перейдите в Settings -> Variables")  
        print("3. Добавьте новую переменную TELEGRAM_SESSION_BASE64")
        print("4. Вставьте значение выше")
        print("5. Deploy заново")
        
        # Сохраняем в файл для удобства
        with open('session_base64.txt', 'w') as f:
            f.write(f"TELEGRAM_SESSION_BASE64={encoded}")
        print()
        print(f"📁 Также сохранено в файл: session_base64.txt")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    convert_session_to_base64()