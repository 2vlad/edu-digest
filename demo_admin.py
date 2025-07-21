#!/usr/bin/env python3
"""
Демонстрация работы админ-панели
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def demo_admin_functionality():
    """Демонстрация функционала админ-панели"""
    print("🌐 Демонстрация Flask админ-панели")
    print("="*45)
    
    try:
        # Импортируем приложение
        from src.admin_panel import app, get_dashboard_stats, get_run_logs
        from src.database import ChannelsDB
        
        with app.app_context():
            print("✅ Flask приложение успешно загружено")
            print(f"   Конфигурация: {app.config.get('DATABASE', 'default')}")
            print(f"   Secret key: {'настроен' if app.secret_key else 'НЕ настроен'}")
            
            # Демонстрируем получение статистики
            print("\n📊 Статистика дашборда:")
            stats = get_dashboard_stats()
            for key, value in stats.items():
                if key != 'last_run':
                    print(f"   {key}: {value}")
            
            # Демонстрируем работу с каналами
            print("\n📺 Активные каналы:")
            channels = ChannelsDB.get_active_channels()
            for channel in channels:
                print(f"   {channel['username']} - {channel['display_name']} (приоритет: {channel['priority']})")
            
            # Демонстрируем логи
            print("\n📋 Последние запуски:")
            logs = get_run_logs(3)
            for log in logs:
                status = log['status']
                time = log['started_at'][:19] if log['started_at'] else 'N/A'
                print(f"   [{time}] {status} - каналов: {log['channels_processed'] or 0}, новостей: {log['news_published'] or 0}")
            
            print(f"\n🌐 Админ-панель готова к запуску:")
            print(f"   Команда: python main.py admin")
            print(f"   URL: http://localhost:5002")
            
            print(f"\n💡 Доступные страницы:")
            routes = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint != 'static' and 'GET' in rule.methods:
                    routes.append(rule.rule)
            
            main_routes = ['/', '/channels', '/channels/add', '/settings', '/logs', '/health']
            for route in main_routes:
                if route in routes:
                    print(f"   ✅ {route}")
                else:
                    print(f"   ❌ {route}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка демонстрации: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_admin_functionality()
    if success:
        print("\n🎉 Админ-панель полностью готова к работе!")
    else:
        print("\n❌ Есть проблемы с админ-панелью")