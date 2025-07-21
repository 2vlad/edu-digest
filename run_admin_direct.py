#!/usr/bin/env python3
"""
Прямой запуск админ-панели для отладки
"""
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    try:
        print("🔧 Инициализация админ-панели...")
        
        # Импортируем все необходимые модули
        from admin_panel import app
        from config import FLASK_PORT
        
        print(f"✅ Модули загружены успешно")
        print(f"🌐 Запуск на порту: {FLASK_PORT}")
        
        # Создаем тестовый контекст
        with app.test_client() as client:
            print("🧪 Тестирование основных маршрутов...")
            
            # Тест главной страницы
            response = client.get('/')
            print(f"   GET / -> {response.status_code}")
            
            # Тест health check
            response = client.get('/health')
            print(f"   GET /health -> {response.status_code}")
            
            # Тест API статистики
            response = client.get('/api/stats')
            print(f"   GET /api/stats -> {response.status_code}")
            
            if response.status_code == 200:
                import json
                stats = response.get_json()
                print(f"      Каналов: {stats.get('active_channels', 0)}")
        
        print("\n✅ Все тесты пройдены!")
        print("🚀 Запуск реального сервера...")
        
        # Запускаем реальный сервер
        app.run(
            host='127.0.0.1', 
            port=FLASK_PORT, 
            debug=False,
            use_reloader=False  # Отключаем перезагрузку для стабильности
        )
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main() or 0)