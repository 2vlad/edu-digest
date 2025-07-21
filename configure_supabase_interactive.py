#!/usr/bin/env python3
"""
Интерактивная настройка Supabase
"""

import os
import re

def main():
    print("🔧 ИНТЕРАКТИВНАЯ НАСТРОЙКА SUPABASE")
    print("=" * 60)
    
    print("\n📋 ДЛЯ НАСТРОЙКИ ВАМ ПОНАДОБИТСЯ:")
    print("1. Проект в Supabase (https://supabase.com)")
    print("2. Project URL из Settings → API")
    print("3. anon public key из Settings → API")
    print("4. Connection string из Settings → Database")
    print()
    
    # Проверяем есть ли уже настройка
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
            
        if 'your-project-ref.supabase.co' in env_content:
            print("📝 ТЕКУЩИЕ PLACEHOLDER'Ы В .ENV:")
            print("   SUPABASE_URL=\"https://your-project-ref.supabase.co\"")
            print("   SUPABASE_ANON_KEY=\"your-anon-public-key-here\"")
            print("   DATABASE_URL=\"postgresql://postgres:your-password@...\"")
            print()
        else:
            print("✅ .env файл уже содержит настройки Supabase")
            response = input("🤔 Перенастроить? (y/N): ").lower()
            if response != 'y':
                print("✅ Настройка пропущена")
                return
    
    print("🚀 ИНТЕРАКТИВНАЯ НАСТРОЙКА:")
    print("-" * 30)
    
    # Получаем данные от пользователя
    print("1️⃣ SUPABASE_URL")
    print("   Получите в Supabase Dashboard → Settings → API → Project URL")
    print("   Пример: https://abcdefghijk.supabase.co")
    supabase_url = input("   Введите SUPABASE_URL: ").strip()
    
    if not supabase_url.startswith('https://') or '.supabase.co' not in supabase_url:
        print("❌ Неверный формат URL. Должен быть: https://xxxxxx.supabase.co")
        return False
    
    print("\n2️⃣ SUPABASE_ANON_KEY")
    print("   Получите в Supabase Dashboard → Settings → API → anon public")
    print("   Пример: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...")
    anon_key = input("   Введите SUPABASE_ANON_KEY: ").strip()
    
    if len(anon_key) < 50:
        print("❌ Ключ слишком короткий. Убедитесь что скопировали полностью")
        return False
    
    print("\n3️⃣ DATABASE_URL")  
    print("   Получите в Supabase Dashboard → Settings → Database → Connection string → URI")
    print("   Пример: postgresql://postgres:password@db.abcdefg.supabase.co:5432/postgres")
    database_url = input("   Введите DATABASE_URL: ").strip()
    
    if not database_url.startswith('postgresql://') or 'supabase.co' not in database_url:
        print("❌ Неверный формат DATABASE_URL")
        return False
    
    # Обновляем .env файл
    print("\n4️⃣ ОБНОВЛЕНИЕ .ENV ФАЙЛА")
    print("-" * 30)
    
    try:
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Заменяем значения
        env_content = re.sub(
            r'SUPABASE_URL="[^"]*"',
            f'SUPABASE_URL="{supabase_url}"',
            env_content
        )
        
        env_content = re.sub(
            r'SUPABASE_ANON_KEY="[^"]*"',
            f'SUPABASE_ANON_KEY="{anon_key}"',
            env_content
        )
        
        env_content = re.sub(
            r'DATABASE_URL="[^"]*"',
            f'DATABASE_URL="{database_url}"',
            env_content
        )
        
        # Сохраняем
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("✅ .env файл обновлен!")
        
        # Проверяем результат
        print("\n5️⃣ ПРОВЕРКА НАСТРОЙКИ")
        print("-" * 30)
        print("🧪 Запускаем тест подключения...")
        
        # Перезагружаем окружение и тестируем
        os.system("source venv/bin/activate && python -c 'import sys; sys.path.append(\"src\"); from src.config import SUPABASE_URL; print(f\"✅ URL загружен: {SUPABASE_URL[:30]}...\")'")
        
        print("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
        print("📋 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Запустите: python setup_supabase_local.py")
        print("2. Затем: python test_local_supabase.py")
        print("3. Или сразу: python test_local_supabase.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления .env файла: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Настройка не завершена")
        print("💡 Убедитесь что у вас есть проект в Supabase и правильные credentials")
    else:
        print("\n✅ Готово! Теперь можете тестировать с Supabase")