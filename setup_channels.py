#!/usr/bin/env python3
"""
Настройка каналов для мониторинга EdTech новостей
"""

import sys
import os
sys.path.append('src')

from src.db_adapter import ChannelsDB, init_database, test_db

# Список популярных EdTech каналов для мониторинга
EDTECH_CHANNELS = [
    {"username": "@edtexno", "display_name": "EdTechno", "priority": 10},
    {"username": "@vc_edtech", "display_name": "VC EdTech", "priority": 9},
    {"username": "@rusedweek", "display_name": "Russian EdWeek", "priority": 8},
    {"username": "@edcrunch", "display_name": "EdCrunch", "priority": 8},
    {"username": "@habr_career", "display_name": "Хабр Карьера", "priority": 7},
    {"username": "@learning_bay", "display_name": "Learning Bay", "priority": 6},
    {"username": "@te_st_channel", "display_name": "Образование которое мы заслужили", "priority": 5},
]

def setup_edtech_channels():
    """Добавляет EdTech каналы в систему"""
    
    print("🚀 Настройка EdTech каналов для мониторинга")
    print("=" * 50)
    
    # Инициализируем базу данных
    print("📊 Инициализация базы данных...")
    try:
        init_database()
        if test_db():
            print("✅ База данных готова")
        else:
            print("❌ Проблема с базой данных")
            return False
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return False
    
    # Добавляем каналы
    added_count = 0
    updated_count = 0
    
    print("\n📺 Добавление каналов...")
    for channel in EDTECH_CHANNELS:
        try:
            channel_id = ChannelsDB.add_channel(
                username=channel["username"],
                display_name=channel["display_name"], 
                priority=channel["priority"]
            )
            print(f"✅ Добавлен: {channel['display_name']} ({channel['username']}) - ID: {channel_id}")
            added_count += 1
            
        except Exception as e:
            if "уже существует" in str(e) or "UNIQUE constraint failed" in str(e):
                print(f"⚠️  Уже существует: {channel['display_name']} ({channel['username']})")
                updated_count += 1
            else:
                print(f"❌ Ошибка добавления {channel['username']}: {e}")
    
    print(f"\n📊 Результат:")
    print(f"   ✅ Добавлено новых каналов: {added_count}")
    print(f"   ⚠️  Уже существовало: {updated_count}")
    print(f"   📺 Всего каналов в системе: {added_count + updated_count}")
    
    # Проверим что каналы добавлены
    try:
        active_channels = ChannelsDB.get_active_channels()
        print(f"\n🔍 Проверка: найдено {len(active_channels)} активных каналов")
        
        for channel in active_channels[:3]:  # Показываем первые 3
            print(f"   • {channel['display_name']} (@{channel['username'].replace('@', '')}) - приоритет {channel['priority']}")
        
        if len(active_channels) > 3:
            print(f"   ... и еще {len(active_channels) - 3} каналов")
            
        return len(active_channels) > 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки каналов: {e}")
        return False

if __name__ == "__main__":
    success = setup_edtech_channels()
    
    if success:
        print("\n🎉 Каналы успешно настроены!")
        print("💡 Теперь можно запускать сбор новостей через админ-панель")
    else:
        print("\n❌ Ошибка настройки каналов")
        
    print("\n🔄 Перезапустите приложение и проверьте админ-панель")