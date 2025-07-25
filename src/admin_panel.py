#!/usr/bin/env python3
"""
Веб-интерфейс (админ-панель) для управления EdTech News Digest Bot
ТОЛЬКО SUPABASE - БЕЗ SQLite FALLBACK
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import session as flask_session

# Настройка логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/admin.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting Admin Panel - SUPABASE ONLY MODE")

# Импортируем конфигурацию и модули базы данных
try:
    logger.info("📦 Attempting relative import...")
    from .database import (
        ChannelsDB, SettingsDB, ProcessedMessagesDB,
        create_connection, test_db, init_database, get_database_info
    )
    from .config import FLASK_SECRET_KEY, FLASK_PORT, TARGET_CHANNEL
    logger.info("✅ Relative import successful")
except ImportError:
    logger.info("📦 Falling back to absolute import...")
    from database import (
        ChannelsDB, SettingsDB, ProcessedMessagesDB,
        create_connection, test_db, init_database, get_database_info
    )
    from config import FLASK_SECRET_KEY, FLASK_PORT, TARGET_CHANNEL
    logger.info("✅ Absolute import successful")

# Инициализация Flask приложения
logger.info("🌐 Initializing Flask application...")
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Настройка папки с шаблонами
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
app.template_folder = template_dir
logger.info(f"📁 Template directory: {template_dir}")
logger.info("✅ Flask app initialized")

# Получаем информацию о базе данных
logger.info("🔍 Getting database information...")
db_info = get_database_info()
logger.info(f"🗄️ Database configuration: {db_info}")
print(f"🗄️ Database configuration: {db_info['type']}")

def get_db():
    """Получение подключения к базе данных"""
    return create_connection()

def get_dashboard_stats_rest_api():
    """Получение статистики через REST API (fallback)"""
    logger.info("📡 Getting dashboard statistics via REST API...")
    
    try:
        from .database import supabase_db
        
        # Получаем каналы
        channels = supabase_db.execute_rest_query('channels', 'GET')
        active_channels = len([c for c in channels if c.get('is_active', True)])
        total_channels = len(channels)
        
        # Обработанные сообщения (пока заглушка, так как сложный запрос)
        try:
            messages = supabase_db.execute_rest_query('processed_messages', 'GET')
            recent_messages = len(messages)  # Упрощенно - все сообщения
        except:
            recent_messages = 0
        
        # Настройки (заглушка)
        published_news = 0
        last_run = None
        
        stats = {
            'active_channels': active_channels,
            'total_channels': total_channels,
            'recent_messages': recent_messages,
            'published_news': published_news,
            'last_run': last_run
        }
        
        logger.info(f"✅ REST API statistics: active={active_channels}, total={total_channels}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ REST API fallback failed: {e}")
        return {
            'active_channels': 0,
            'total_channels': 0,
            'recent_messages': 0,
            'published_news': 0,
            'last_run': None,
            'error': f'REST API error: {str(e)}'
        }

def get_dashboard_stats():
    """Получение статистики для дашборда"""
    logger.info("📊 Getting dashboard statistics...")
    
    conn = None
    try:
        logger.info("🔗 Getting database connection...")
        conn = get_db()
        
        if conn is None:
            logger.warning("⚠️ PostgreSQL connection unavailable, using REST API fallback...")
            return get_dashboard_stats_rest_api()
            
        cursor = conn.cursor()
        logger.info("✅ Database connection established")
        
        # Проверяем существование таблиц
        logger.info("🔍 Checking if tables exist...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [row['table_name'] if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Available tables: {tables}")
        
        if 'channels' not in tables:
            logger.error("❌ Table 'channels' does not exist!")
            # Пытаемся создать таблицы
            try:
                logger.info("⚡ Attempting to create missing tables...")
                init_database()
                logger.info("✅ Tables created successfully")
            except Exception as init_error:
                logger.error(f"❌ Failed to create tables: {init_error}")
                raise
        
        # Общее количество каналов
        logger.info("📈 Querying active channels count...")
        cursor.execute('SELECT COUNT(*) FROM channels WHERE is_active = true')
        result = cursor.fetchone()
        active_channels = result['count'] if isinstance(result, dict) else result[0]
        
        # Общее количество каналов
        cursor.execute('SELECT COUNT(*) FROM channels')
        result = cursor.fetchone()
        total_channels = result['count'] if isinstance(result, dict) else result[0]
        
        # Количество обработанных сообщений за последние 24 часа
        cursor.execute('''
            SELECT COUNT(*) FROM processed_messages 
            WHERE processed_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ''')
        result = cursor.fetchone()
        recent_messages = result['count'] if isinstance(result, dict) else result[0]
        
        # Количество опубликованных новостей за последние 24 часа
        cursor.execute('''
            SELECT COUNT(*) FROM processed_messages 
            WHERE published = true AND processed_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ''')
        result = cursor.fetchone()
        published_news = result['count'] if isinstance(result, dict) else result[0]
        
        # Последний запуск
        cursor.execute('SELECT * FROM run_logs ORDER BY started_at DESC LIMIT 1')
        last_run = cursor.fetchone()
        
        # Количество успешных запусков за последние 24 часа
        cursor.execute('''
            SELECT COUNT(*) FROM run_logs 
            WHERE status = 'completed' AND started_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ''')
        result = cursor.fetchone()
        successful_runs_24h = result['count'] if isinstance(result, dict) else result[0]
        
        # Количество опубликованных новостей за последние 24 часа из run_logs
        cursor.execute('''
            SELECT COALESCE(SUM(news_published), 0) as total FROM run_logs 
            WHERE status = 'completed' AND started_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ''')
        result = cursor.fetchone()
        news_published_24h = result['total'] if isinstance(result, dict) else result[0]
        
        # Количество собранных сообщений за последние 24 часа из run_logs
        cursor.execute('''
            SELECT COALESCE(SUM(messages_collected), 0) as total FROM run_logs 
            WHERE started_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ''')
        result = cursor.fetchone()
        messages_collected_24h = result['total'] if isinstance(result, dict) else result[0]
        
        stats = {
            'active_channels': active_channels,
            'total_channels': total_channels,
            'recent_messages': recent_messages,
            'published_news': published_news,
            'successful_runs_24h': successful_runs_24h,
            'news_published_24h': news_published_24h,
            'messages_collected_24h': messages_collected_24h,
            'last_run': dict(last_run) if last_run else None
        }
        
        logger.info(f"📊 Dashboard stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard stats: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return {
            'active_channels': 0,
            'total_channels': 0,
            'recent_messages': 0,
            'published_news': 0,
            'last_run': None,
            'error': str(e)
        }

# Маршруты (Routes)

@app.route('/')
def dashboard():
    """Главная страница - дашборд"""
    logger.info("🌐 Dashboard route accessed")
    
    # Обеспечиваем инициализацию БД при первом доступе
    try:
        logger.info("📦 Setting up database connection...")
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
        logger.info("📊 Getting dashboard statistics...")
        stats = get_dashboard_stats()
        logger.info("✅ Dashboard statistics retrieved")
    except Exception as e:
        logger.error(f"❌ Error getting dashboard stats: {e}")
        stats = {
            'active_channels': 0,
            'total_channels': 0,
            'recent_messages': 0,
            'published_news': 0,
            'last_run': None,
            'error': str(e)
        }
    
    # Получаем топ каналы
    try:
        logger.info("📺 Getting top channels...")
        channels = ChannelsDB.get_active_channels()[:5]  # Топ 5 каналов
        logger.info(f"✅ Retrieved {len(channels)} top channels")
    except Exception as e:
        logger.error(f"❌ Error getting channels: {e}")
        channels = []
    
    # Получаем последние настройки
    try:
        logger.info("⚙️ Getting current settings...")
        current_settings = {
            'max_news_count': SettingsDB.get_setting('max_news_count', '7'),
            'target_channel': SettingsDB.get_setting('target_channel', TARGET_CHANNEL),
            'digest_times': SettingsDB.get_setting('digest_times', '12:00,18:00'),
            'hours_lookback': SettingsDB.get_setting('hours_lookback', '12')
        }
        logger.info("✅ Current settings retrieved")
    except Exception as e:
        logger.error(f"❌ Error getting settings: {e}")
        current_settings = {
            'max_news_count': '7',
            'target_channel': TARGET_CHANNEL,
            'digest_times': '12:00,18:00',
            'hours_lookback': '12'
        }
    
    # Получаем последние запуски для блока "Последние запуски"
    recent_logs = []
    try:
        logger.info("📜 Getting recent run logs...")
        conn = get_db()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM run_logs 
                ORDER BY started_at DESC 
                LIMIT 10
            ''')
            recent_logs = [dict(row) for row in cursor.fetchall()]
            logger.info(f"✅ Retrieved {len(recent_logs)} recent logs")
        else:
            logger.warning("⚠️ No connection for recent logs")
    except Exception as e:
        logger.error(f"❌ Error getting recent logs: {e}")
        recent_logs = []
    
    logger.info("✅ Dashboard data prepared, rendering template")
    
    return render_template('dashboard.html',
                         stats=stats,
                         channels=channels,
                         settings=current_settings,
                         db_info=db_info,
                         recent_logs=recent_logs)

@app.route('/channels')
def channels():
    """Страница управления каналами"""
    logger.info("📺 Channels page accessed")
    
    try:
        channels_list = ChannelsDB.get_active_channels()
        logger.info(f"✅ Retrieved {len(channels_list)} channels")
    except Exception as e:
        logger.error(f"❌ Error getting channels: {e}")
        channels_list = []
        flash(f'Ошибка получения каналов: {e}', 'error')
    
    return render_template('channels.html', channels=channels_list)

@app.route('/channels/add')
def add_channel_form():
    """Страница формы добавления канала"""
    logger.info("➕ Add channel form accessed")
    return render_template('add_channel.html')

@app.route('/add_channel', methods=['POST'])
def add_channel():
    """Добавление нового канала"""
    logger.info("➕ Add channel request received")
    
    username = request.form.get('username', '').strip()
    display_name = request.form.get('display_name', '').strip()
    priority = request.form.get('priority', 0, type=int)
    
    logger.info(f"📋 Channel data: {username}, {display_name}, priority={priority}")
    
    if not username:
        flash('Имя канала обязательно', 'error')
        return redirect(url_for('channels'))
    
    # Добавляем @ если отсутствует
    if not username.startswith('@'):
        username = '@' + username
    
    try:
        channel_id = ChannelsDB.add_channel(username, display_name, priority)
        flash(f'Канал {username} успешно добавлен (ID: {channel_id})', 'success')
        logger.info(f"✅ Channel {username} added successfully with ID {channel_id}")
    except ValueError as e:
        flash(str(e), 'error')
        logger.warning(f"⚠️ Channel addition failed: {e}")
    except Exception as e:
        flash(f'Ошибка добавления канала: {e}', 'error')
        logger.error(f"❌ Channel addition error: {e}")
    
    return redirect(url_for('channels'))

@app.route('/test')
def test_route():
    """Тестовый роут для проверки"""
    return "Test route works!"

@app.route('/channels/<int:channel_id>/edit')
def edit_channel_form(channel_id):
    """Страница формы редактирования канала"""
    logger.info(f"✏️ Edit channel form accessed for ID: {channel_id}")
    
    try:
        # Получаем данные канала
        channels = ChannelsDB.get_active_channels()
        channel = None
        for ch in channels:
            if ch.get('id') == channel_id:
                channel = ch
                break
        
        if not channel:
            flash('Канал не найден', 'error')
            return redirect(url_for('channels'))
        
        logger.info(f"✅ Channel {channel_id} found for editing")
        return render_template('edit_channel.html', channel=channel)
        
    except Exception as e:
        flash(f'Ошибка получения данных канала: {e}', 'error')
        logger.error(f"❌ Error getting channel {channel_id}: {e}")
        return redirect(url_for('channels'))

@app.route('/channels/<int:channel_id>/update', methods=['POST'])
def update_channel(channel_id):
    """Обновление канала"""
    logger.info(f"✏️ Update channel request received for ID: {channel_id}")
    
    username = request.form.get('username', '').strip()
    display_name = request.form.get('display_name', '').strip()
    priority = request.form.get('priority', 0, type=int)
    is_active = 'is_active' in request.form
    
    logger.info(f"📋 Channel update data: {username}, {display_name}, priority={priority}, active={is_active}")
    
    if not username:
        flash('Имя канала обязательно', 'error')
        return redirect(url_for('edit_channel_form', channel_id=channel_id))
    
    # Добавляем @ если отсутствует
    if not username.startswith('@'):
        username = '@' + username
    
    try:
        # Обновляем канал
        result = ChannelsDB.update_channel(channel_id, username, display_name, priority, is_active)
        if result:
            flash('Канал успешно обновлен', 'success')
            logger.info(f"✅ Channel {channel_id} updated successfully")
        else:
            flash('Ошибка обновления канала', 'error')
            logger.error(f"❌ Failed to update channel {channel_id}")
    except Exception as e:
        flash(f'Ошибка обновления канала: {e}', 'error')
        logger.error(f"❌ Channel update error: {e}")
    
    return redirect(url_for('channels'))

@app.route('/channels/<int:channel_id>/delete', methods=['POST', 'GET'])
def delete_channel(channel_id):
    """Удаление канала"""
    logger.info(f"🗑️ Delete channel request received for ID: {channel_id}")
    
    try:
        # Удаляем канал через REST API или PostgreSQL
        result = ChannelsDB.delete_channel(channel_id)
        if result:
            flash('Канал успешно удален', 'success')
            logger.info(f"✅ Channel {channel_id} deleted successfully")
        else:
            flash('Ошибка удаления канала', 'error')
            logger.error(f"❌ Failed to delete channel {channel_id}")
    except Exception as e:
        flash(f'Ошибка удаления канала: {e}', 'error')
        logger.error(f"❌ Channel deletion error: {e}")
    
    return redirect(url_for('channels'))

@app.route('/channels/<int:channel_id>/toggle', methods=['POST', 'GET'])
def toggle_channel(channel_id):
    """Включение/выключение канала"""
    logger.info(f"🔄 Toggle channel request received for ID: {channel_id}")
    
    try:
        # Переключаем статус канала
        result = ChannelsDB.toggle_channel_status(channel_id)
        if result:
            flash('Статус канала изменен', 'success')
            logger.info(f"✅ Channel {channel_id} status toggled successfully")
        else:
            flash('Ошибка изменения статуса канала', 'error')
            logger.error(f"❌ Failed to toggle channel {channel_id}")
    except Exception as e:
        flash(f'Ошибка изменения статуса: {e}', 'error')
        logger.error(f"❌ Channel toggle error: {e}")
    
    return redirect(url_for('channels'))

@app.route('/settings')
def settings():
    """Страница настроек"""
    logger.info("⚙️ Settings page accessed")
    
    try:
        current_settings = {
            'max_news_count': SettingsDB.get_setting('max_news_count', '7'),
            'target_channel': SettingsDB.get_setting('target_channel', TARGET_CHANNEL),
            'digest_times': SettingsDB.get_setting('digest_times', '12:00,18:00'),
            'hours_lookback': SettingsDB.get_setting('hours_lookback', '12'),
            'summary_max_length': SettingsDB.get_setting('summary_max_length', '150')
        }
        logger.info("✅ Current settings retrieved")
    except Exception as e:
        logger.error(f"❌ Error getting settings: {e}")
        current_settings = {}
        flash(f'Ошибка получения настроек: {e}', 'error')
    
    return render_template('settings.html', settings=current_settings)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Обновление настроек"""
    logger.info("🔧 Update settings request received")
    
    try:
        # Получаем данные из формы
        max_news_count = request.form.get('max_news_count', '7')
        target_channel = request.form.get('target_channel', TARGET_CHANNEL)
        digest_times = request.form.get('digest_times', '12:00,18:00')
        hours_lookback = request.form.get('hours_lookback', '12')
        summary_max_length = request.form.get('summary_max_length', '150')
        
        # Обновляем настройки
        SettingsDB.set_setting('max_news_count', max_news_count, 'Максимальное количество новостей в дайджесте')
        SettingsDB.set_setting('target_channel', target_channel, 'Целевой канал для публикации')
        SettingsDB.set_setting('digest_times', digest_times, 'Время публикации дайджестов')
        SettingsDB.set_setting('hours_lookback', hours_lookback, 'Сколько часов назад искать новости')
        SettingsDB.set_setting('summary_max_length', summary_max_length, 'Максимальная длина суммаризации')
        
        flash('Настройки успешно обновлены', 'success')
        logger.info("✅ Settings updated successfully")
        
    except Exception as e:
        flash(f'Ошибка обновления настроек: {e}', 'error')
        logger.error(f"❌ Settings update error: {e}")
    
    return redirect(url_for('settings'))

@app.route('/logs')
def logs():
    """Страница логов"""
    logger.info("📋 Logs page accessed")
    
    try:
        conn = get_db()
        if conn is None:
            logger.warning("⚠️ PostgreSQL недоступен для получения логов")
            run_logs = []
            flash('База данных недоступна. Логи не могут быть загружены.', 'warning')
        else:
            cursor = conn.cursor()
            
            # Получаем последние запуски
            cursor.execute('''
                SELECT * FROM run_logs 
                ORDER BY started_at DESC 
                LIMIT 50
            ''')
            run_logs = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"✅ Retrieved {len(run_logs)} log entries")
        
    except Exception as e:
        logger.error(f"❌ Error getting logs: {e}")
        run_logs = []
        flash(f'Ошибка получения логов: {e}', 'error')
    
    return render_template('logs.html', logs=run_logs)

# API endpoint for stats (for frontend auto-refresh)
@app.route('/api/stats')
def api_stats():
    """API endpoint для получения статистики"""
    try:
        stats = get_dashboard_stats()
        return jsonify({
            'status': 'ok',
            'active_channels': stats.get('active_channels', 0),
            'total_channels': stats.get('total_channels', 0),
            'messages_today': stats.get('messages_today', 0),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Error in /api/stats: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

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
            if conn is None:
                # Используем REST API fallback
                from .database import supabase_db
                channels_data = supabase_db.execute_rest_query('channels', 'GET')
                channels_count = len(channels_data) if channels_data else 0
            else:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM channels')
                result = cursor.fetchone()
                channels_count = result['count'] if isinstance(result, dict) else result[0]
            
            basic_info.update({
                'database': 'connected',
                'database_exists': True,
                'channels_count': channels_count
            })
            
        except Exception as db_error:
            basic_info.update({
                'database': f'error: {str(db_error)}',
                'database_exists': False,
                'channels_count': 0
            })
        
        return jsonify(basic_info)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/run-collect', methods=['GET', 'POST'])
def run_collect():
    """Запуск сбора новостей"""
    logger.info("🚀 Запуск сбора новостей из админ-панели...")
    
    try:
        import asyncio
        import sys
        import os
        
        # Добавляем путь к main.py
        main_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        if main_path not in sys.path:
            sys.path.append(main_path)
        
        # Импортируем функцию из main.py
        from main import run_collect as main_run_collect
        
        # Запускаем сбор новостей
        logger.info("🔄 Запуск асинхронной функции сбора новостей...")
        
        # Создаем новый event loop для асинхронного выполнения
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result_code = loop.run_until_complete(main_run_collect())
            
            if result_code == 0:
                flash("✅ Сбор новостей завершен успешно!", "success")
                logger.info("✅ Сбор новостей завершен успешно")
            else:
                flash("❌ Ошибка при сборе новостей. Проверьте логи.", "error")
                logger.error("❌ Сбор новостей завершился с ошибкой")
                
        finally:
            loop.close()
        
    except ImportError as ie:
        error_msg = f"Ошибка импорта: {str(ie)}"
        logger.error(f"❌ {error_msg}")
        flash(f"❌ {error_msg}", "error")
        
    except Exception as e:
        error_msg = f"Ошибка запуска сбора новостей: {str(e)}"
        logger.error(f"❌ {error_msg}")
        flash(f"❌ {error_msg}", "error")
    
    # Возвращаемся на главную страницу
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    logger.info(f"🚀 Starting Flask development server on port {FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=True)