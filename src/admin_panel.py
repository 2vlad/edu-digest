#!/usr/bin/env python3
"""
Task 6: Flask админ-панель для управления каналами
Веб-интерфейс для управления EdTech News Digest Bot
СТРОГО ТОЛЬКО SUPABASE MODE!
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Настройка детального логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/admin_panel.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting Admin Panel - SUPABASE ONLY MODE")

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

try:
    # Попытка относительного импорта (при запуске через main.py)
    logger.info("📦 Attempting relative import...")
    from .db_adapter import (ChannelsDB, ProcessedMessagesDB, SettingsDB, 
                            create_connection, get_database_info)
    from .config import FLASK_SECRET_KEY, FLASK_PORT
    logger.info("✅ Relative import successful")
except ImportError as e:
    # Абсолютный импорт (при прямом запуске)
    logger.info(f"🔄 Relative import failed: {e}, trying absolute import...")
    try:
        from db_adapter import (ChannelsDB, ProcessedMessagesDB, SettingsDB, 
                               create_connection, get_database_info)
        from config import FLASK_SECRET_KEY, FLASK_PORT
        logger.info("✅ Absolute import successful")
    except ImportError as abs_error:
        logger.error(f"❌ Both imports failed: relative={e}, absolute={abs_error}")
        raise

# Инициализация Flask приложения
logger.info("🌐 Initializing Flask application...")
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
logger.info(f"📁 Template directory: {template_dir}")
app = Flask(__name__, template_folder=template_dir)
app.secret_key = FLASK_SECRET_KEY
logger.info("✅ Flask app initialized")

# Конфигурация базы данных
logger.info("🔍 Getting database information...")
db_info = get_database_info()
app.config['DATABASE_INFO'] = db_info
logger.info(f"🗄️ Database configuration: {db_info}")
print(f"🗄️ Database configuration: {db_info['type']}")

# Функции для работы с данными
def get_db():
    """Получение подключения к базе данных"""
    return create_connection()

def get_run_logs(limit=20):
    """Получение логов запусков"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM run_logs 
            ORDER BY started_at DESC 
            LIMIT ?
        ''', (limit,))
        logs = [dict(row) for row in cursor.fetchall()]
        return logs
    finally:
        conn.close()

def get_dashboard_stats():
    """Получение статистики для дашборда"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("📊 Getting dashboard statistics...")
    
    conn = None
    try:
        logger.info("🔗 Getting database connection...")
        conn = get_db()
        cursor = conn.cursor()
        logger.info("✅ Database connection established")
        
        # Проверяем существование таблиц
        logger.info("🔍 Checking if tables exist...")
        
        if USE_SUPABASE:
            # PostgreSQL запрос
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables = [row['table_name'] if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
        else:
            # SQLite запрос
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
        logger.info(f"📋 Available tables: {tables}")
        
        if 'channels' not in tables:
            logger.error("❌ Table 'channels' does not exist!")
            # Пытаемся создать таблицы
            try:
                from .db_adapter import init_database
                logger.info("⚡ Attempting to create missing tables...")
                init_database()
                logger.info("✅ Tables created successfully")
            except Exception as init_error:
                logger.error(f"❌ Failed to create tables: {init_error}")
                raise
        
        # Общее количество каналов
        logger.info("📈 Querying active channels count...")
        if USE_SUPABASE:
            cursor.execute('SELECT COUNT(*) FROM channels WHERE is_active = true')
            active_channels = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) FROM channels')
            total_channels = cursor.fetchone()['count']
        else:
            cursor.execute('SELECT COUNT(*) FROM channels WHERE is_active = 1')
            active_channels = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM channels')
            total_channels = cursor.fetchone()[0]
            
        logger.info(f"✅ Active channels: {active_channels}")
        logger.info(f"✅ Total channels: {total_channels}")
        
        # Статистика за последние 24 часа
        yesterday = datetime.now() - timedelta(hours=24)
        
        if USE_SUPABASE:
            cursor.execute('''
                SELECT COUNT(*) FROM run_logs 
                WHERE started_at > %s AND status = 'completed'
            ''', (yesterday.isoformat(),))
            successful_runs = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT SUM(news_published) FROM run_logs 
                WHERE started_at > %s AND status = 'completed'
            ''', (yesterday.isoformat(),))
            result = cursor.fetchone()
            news_published_24h = result['sum'] if result and result['sum'] else 0
            
            cursor.execute('''
                SELECT SUM(messages_collected) FROM run_logs 
                WHERE started_at > %s AND status = 'completed'
            ''', (yesterday.isoformat(),))
            result = cursor.fetchone()
            messages_collected_24h = result['sum'] if result and result['sum'] else 0
        else:
            cursor.execute('''
                SELECT COUNT(*) FROM run_logs 
                WHERE started_at > ? AND status = 'completed'
            ''', (yesterday.isoformat(),))
            successful_runs = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT SUM(news_published) FROM run_logs 
                WHERE started_at > ? AND status = 'completed'
            ''', (yesterday.isoformat(),))
            news_published_24h = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT SUM(messages_collected) FROM run_logs 
                WHERE started_at > ? AND status = 'completed'
            ''', (yesterday.isoformat(),))
            messages_collected_24h = cursor.fetchone()[0] or 0
        
        # Последний запуск
        cursor.execute('''
            SELECT * FROM run_logs 
            ORDER BY started_at DESC 
            LIMIT 1
        ''')
        last_run = cursor.fetchone()
        last_run = dict(last_run) if last_run else None
        
        return {
            'active_channels': active_channels,
            'total_channels': total_channels,
            'successful_runs_24h': successful_runs,
            'news_published_24h': news_published_24h,
            'messages_collected_24h': messages_collected_24h,
            'last_run': last_run
        }
    finally:
        if conn:
            conn.close()

# Маршруты (Routes)

@app.route('/')
def dashboard():
    """Главная страница - дашборд"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🌐 Dashboard route accessed")
    
    # Обеспечиваем инициализацию БД при первом доступе
    try:
        logger.info("📦 Setting up database connection...")
        
        # Импортируем необходимые функции из адаптера
        try:
            from .db_adapter import init_database, test_db
            logger.info("✅ Database adapter imported via relative import")
        except ImportError:
            from db_adapter import init_database, test_db
            logger.info("✅ Database adapter imported via absolute import")
        
        logger.info(f"🗄️ Database type: {db_info['type']}")
            
        # Проверяем состояние БД
        logger.info("🔍 Testing database connection...")
        db_exists = test_db()
        logger.info(f"📊 Database test result: {db_exists}")
        
        if not db_exists:
            logger.info("⚡ Database not initialized, initializing now...")
            init_database()
            logger.info("✅ Database initialization completed")
        else:
            logger.info("✅ Database already initialized")
    
    except Exception as e:
        logger.error(f"❌ Database setup error: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        # Продолжаем выполнение, попробуем получить stats
    
    # Получаем статистику
    try:
        logger.info("📊 Getting dashboard stats...")
        stats = get_dashboard_stats()
        logger.info(f"✅ Stats retrieved: {stats}")
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        # Fallback stats
        stats = {
            'active_channels': 0,
            'total_channels': 0,
            'successful_runs_24h': 0,
            'news_published_24h': 0,
            'messages_collected_24h': 0,
            'last_run': None
        }
    
    # Получаем логи
    try:
        logger.info("📜 Getting recent logs...")
        recent_logs = get_run_logs(10)
        logger.info(f"✅ Retrieved {len(recent_logs)} log entries")
    except Exception as e:
        logger.error(f"❌ Error getting logs: {e}")
        recent_logs = []
    
    logger.info("🎨 Rendering template...")
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_logs=recent_logs,
                         title="Дашборд")

@app.route('/channels')
def channels():
    """Страница управления каналами"""
    channels_list = ChannelsDB.get_active_channels()
    
    # Добавляем статистику по каналам
    for channel in channels_list:
        conn = get_db()
        cursor = conn.cursor()
        try:
            # Количество обработанных сообщений за последние 7 дней
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute('''
                SELECT COUNT(*) FROM processed_messages 
                WHERE channel_id = ? AND processed_at > ?
            ''', (channel['id'], week_ago.isoformat()))
            channel['messages_7d'] = cursor.fetchone()[0]
            
            # Последнее обработанное сообщение
            cursor.execute('''
                SELECT processed_at FROM processed_messages 
                WHERE channel_id = ? 
                ORDER BY processed_at DESC 
                LIMIT 1
            ''', (channel['id'],))
            last_message = cursor.fetchone()
            channel['last_message_date'] = last_message[0] if last_message else None
            
        finally:
            conn.close()
    
    return render_template('channels.html', 
                         channels=channels_list,
                         title="Управление каналами")

@app.route('/channels/add', methods=['GET', 'POST'])
def add_channel():
    """Добавление нового канала"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        display_name = request.form['display_name'].strip()
        priority = int(request.form['priority'])
        
        # Валидация
        if not username.startswith('@'):
            username = '@' + username
        
        if not username or not display_name:
            flash('Заполните все обязательные поля', 'error')
            return render_template('add_channel.html', title="Добавить канал")
        
        if not (0 <= priority <= 10):
            flash('Приоритет должен быть от 0 до 10', 'error')
            return render_template('add_channel.html', title="Добавить канал")
        
        try:
            channel_id = ChannelsDB.add_channel(username, display_name, priority)
            flash(f'Канал {display_name} успешно добавлен (ID: {channel_id})', 'success')
            return redirect(url_for('channels'))
        except Exception as e:
            if "уже существует" in str(e):
                flash(f'Канал {username} уже существует', 'error')
            else:
                flash(f'Ошибка добавления канала: {str(e)}', 'error')
    
    return render_template('add_channel.html', title="Добавить канал")

@app.route('/channels/<int:channel_id>/edit', methods=['GET', 'POST'])
def edit_channel(channel_id):
    """Редактирование канала"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        display_name = request.form['display_name'].strip()
        priority = int(request.form['priority'])
        is_active = 'is_active' in request.form
        
        if not display_name:
            flash('Название канала не может быть пустым', 'error')
        elif not (0 <= priority <= 10):
            flash('Приоритет должен быть от 0 до 10', 'error')
        else:
            try:
                cursor.execute('''
                    UPDATE channels 
                    SET display_name = ?, priority = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (display_name, priority, is_active, channel_id))
                conn.commit()
                flash('Канал успешно обновлен', 'success')
                return redirect(url_for('channels'))
            except Exception as e:
                flash(f'Ошибка обновления канала: {str(e)}', 'error')
    
    # Получаем данные канала
    cursor.execute('SELECT * FROM channels WHERE id = ?', (channel_id,))
    channel = cursor.fetchone()
    conn.close()
    
    if not channel:
        flash('Канал не найден', 'error')
        return redirect(url_for('channels'))
    
    return render_template('edit_channel.html', 
                         channel=dict(channel),
                         title=f"Редактировать {channel['display_name']}")

@app.route('/channels/<int:channel_id>/delete', methods=['POST'])
def delete_channel(channel_id):
    """Удаление канала"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем информацию о канале
        cursor.execute('SELECT display_name FROM channels WHERE id = ?', (channel_id,))
        channel = cursor.fetchone()
        
        if not channel:
            flash('Канал не найден', 'error')
        else:
            # Удаляем канал и связанные данные
            cursor.execute('DELETE FROM processed_messages WHERE channel_id = ?', (channel_id,))
            cursor.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
            conn.commit()
            
            flash(f'Канал "{channel[0]}" успешно удален', 'success')
    
    except Exception as e:
        flash(f'Ошибка удаления канала: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('channels'))

@app.route('/settings')
def settings():
    """Страница настроек системы"""
    # Получаем все настройки
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM settings ORDER BY key')
        settings_list = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
    
    return render_template('settings.html', 
                         settings=settings_list,
                         title="Настройки системы")

@app.route('/settings/update', methods=['POST'])
def update_settings():
    """Обновление настроек"""
    try:
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                
                # Валидация некоторых настроек
                if setting_key == 'max_news_count':
                    if not (1 <= int(value) <= 50):
                        flash('Количество новостей должно быть от 1 до 50', 'error')
                        return redirect(url_for('settings'))
                
                elif setting_key == 'hours_lookback':
                    if not (1 <= int(value) <= 168):  # До недели
                        flash('Период поиска должен быть от 1 до 168 часов', 'error')
                        return redirect(url_for('settings'))
                
                SettingsDB.set_setting(setting_key, value)
        
        flash('Настройки успешно обновлены', 'success')
        
    except Exception as e:
        flash(f'Ошибка обновления настроек: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/logs')
def logs():
    """Страница логов запусков"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Общее количество записей
        cursor.execute('SELECT COUNT(*) FROM run_logs')
        total_logs = cursor.fetchone()[0]
        
        # Получаем логи с пагинацией
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT * FROM run_logs 
            ORDER BY started_at DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        logs = [dict(row) for row in cursor.fetchall()]
        
        # Рассчитываем пагинацию
        total_pages = (total_logs + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
    finally:
        conn.close()
    
    return render_template('logs.html',
                         logs=logs,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         title="Логи запусков")

@app.route('/run-collect', methods=['POST'])
def run_collect():
    """Запуск сбора новостей из админки"""
    import logging
    import asyncio
    import signal
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
    
    logger = logging.getLogger(__name__)
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Operation timed out")
    
    try:
        logger.info("🚀 Начинаем запуск сбора новостей из админки...")
        
        # Проверяем наличие необходимых переменных окружения
        required_env_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_BOT_TOKEN', 'ANTHROPIC_API_KEY']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f'Отсутствуют переменные окружения: {", ".join(missing_vars)}'
            logger.error(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('dashboard'))
        
        logger.info("✅ Все переменные окружения найдены")
        
        try:
            from .news_collector import NewsCollector
            logger.info("✅ NewsCollector импортирован через относительный импорт")
        except ImportError:
            from news_collector import NewsCollector
            logger.info("✅ NewsCollector импортирован через абсолютный импорт")
        
        logger.info("🔄 Создаем NewsCollector и запускаем полный цикл...")
        
        # Создаем функцию для выполнения в отдельном потоке
        def run_news_collection():
            try:
                collector = NewsCollector()
                # Создаем новый цикл событий для этого потока
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(collector.run_full_cycle())
                    return result
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"❌ Ошибка в run_news_collection: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {"success": False, "error": str(e)}
        
        # Запускаем с таймаутом 5 минут
        logger.info("⏳ Запускаем сбор новостей с таймаутом 5 минут...")
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_news_collection)
            try:
                result = future.result(timeout=300)  # 5 минут
                logger.info(f"📊 Результат выполнения: {result}")
            except FuturesTimeoutError:
                logger.error("❌ Таймаут: сбор новостей занял более 5 минут")
                future.cancel()
                flash('Таймаут: сбор новостей занял слишком много времени. Попробуйте позже.', 'error')
                return redirect(url_for('dashboard'))
        
        if result.get('success'):
            success_msg = (f'Сбор новостей завершен успешно! '
                          f'Обработано: {result.get("channels_processed", 0)} каналов, '
                          f'опубликовано: {result.get("news_published", 0)} новостей')
            logger.info(f"✅ {success_msg}")
            flash(success_msg, 'success')
        else:
            error_msg = f'Ошибка сбора новостей: {result.get("error", "Неизвестная ошибка")}'
            logger.error(f"❌ {error_msg}")
            flash(error_msg, 'error')
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f'Ошибка запуска сбора: {str(e)}'
        logger.error(f"❌ {error_msg}")
        logger.error(f"📋 Полная трассировка:\n{error_details}")
        flash(error_msg, 'error')
    
    return redirect(url_for('dashboard'))

# API endpoints для AJAX запросов
@app.route('/api/stats')
def api_stats():
    """API для получения статистики"""
    stats = get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/channels')
def api_channels():
    """API для получения списка каналов"""
    channels_list = ChannelsDB.get_active_channels()
    return jsonify(channels_list)

# Health check endpoint для Railway
@app.route('/health')
def health():
    """Health check для мониторинга"""
    try:
        # Получаем информацию о базе данных
        db_info = get_database_info()
        
        # Простая проверка - возвращаем OK без сложной инициализации
        basic_info = {
            'status': 'ok',
            'database_type': db_info['type'],
            'database_persistent': db_info.get('persistent', False),
            'railway_compatible': db_info.get('railway_compatible', False),
            'is_railway': bool(os.getenv('RAILWAY_ENVIRONMENT')),
            'timestamp': datetime.now().isoformat()
        }
        
        # Пробуем подключиться к БД для проверки
        try:
            conn = get_db()
            if USE_SUPABASE:
                # PostgreSQL проверка
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM channels')
                result = cursor.fetchone()
                channels_count = result['count'] if isinstance(result, dict) else result[0]
            else:
                # SQLite проверка
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM channels')
                channels_count = cursor.fetchone()[0]
                conn.close()
            
            basic_info.update({
                'database': 'connected',
                'channels_count': channels_count
            })
            
        except Exception as db_error:
            basic_info.update({
                'database': f'error: {str(db_error)}',
                'channels_count': 0
            })
        
        return jsonify(basic_info)
    
    except Exception as e:
        # Минимальный error response чтобы не крашить health check
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 200  # Возвращаем 200, чтобы не вызвать рестарт

# Создание HTML шаблонов
def create_templates():
    """Создание директории и HTML шаблонов"""
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    os.makedirs(template_dir, exist_ok=True)
    
    # Base template
    base_template = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}EdTech News Digest - Админ-панель{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot"></i> EdTech News Bot
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-tachometer-alt"></i> Дашборд</a>
                <a class="nav-link" href="/channels"><i class="fas fa-list"></i> Каналы</a>
                <a class="nav-link" href="/settings"><i class="fas fa-cog"></i> Настройки</a>
                <a class="nav-link" href="/logs"><i class="fas fa-file-text"></i> Логи</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    with open(os.path.join(template_dir, 'base.html'), 'w', encoding='utf-8') as f:
        f.write(base_template)

# Инициализация при импорте
if __name__ == '__main__':
    # Создаем шаблоны если их нет
    create_templates()
    
    print("🌐 Flask админ-панель запущена!")
    print(f"📍 Адрес: http://localhost:{FLASK_PORT}")
    print("🔧 Доступные функции:")
    print("   - Управление каналами (добавление, редактирование, удаление)")
    print("   - Настройки системы")
    print("   - Просмотр логов запусков")
    print("   - Запуск сбора новостей")
    print("   - API endpoints")
    print("   - Health check")
    
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
else:
    # При импорте создаем шаблоны
    create_templates()