#!/usr/bin/env python3
"""
Task 6: Flask админ-панель для управления каналами
Веб-интерфейс для управления EdTech News Digest Bot
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

try:
    # Попытка относительного импорта (при запуске через main.py)
    from .database import (ChannelsDB, ProcessedMessagesDB, SettingsDB, 
                          create_connection, DATABASE_PATH)
    from .config import FLASK_SECRET_KEY, FLASK_PORT
except ImportError:
    # Абсолютный импорт (при прямом запуске)
    from database import (ChannelsDB, ProcessedMessagesDB, SettingsDB, 
                         create_connection, DATABASE_PATH)
    from config import FLASK_SECRET_KEY, FLASK_PORT

# Инициализация Flask приложения
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = FLASK_SECRET_KEY
app.config['DATABASE'] = DATABASE_PATH

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
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Общее количество каналов
        cursor.execute('SELECT COUNT(*) FROM channels WHERE is_active = 1')
        active_channels = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM channels')
        total_channels = cursor.fetchone()[0]
        
        # Статистика за последние 24 часа
        yesterday = datetime.now() - timedelta(hours=24)
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
        conn.close()

# Маршруты (Routes)

@app.route('/')
def dashboard():
    """Главная страница - дашборд"""
    stats = get_dashboard_stats()
    recent_logs = get_run_logs(10)
    
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
    try:
        import asyncio
        try:
            from .news_collector import NewsCollector
        except ImportError:
            from news_collector import NewsCollector
        
        # Создаем новый цикл событий для async функции
        collector = NewsCollector()
        result = asyncio.run(collector.run_full_cycle())
        
        if result['success']:
            flash(f'Сбор новостей завершен успешно! '
                  f'Обработано: {result["channels_processed"]} каналов, '
                  f'опубликовано: {result["news_published"]} новостей', 'success')
        else:
            flash(f'Ошибка сбора новостей: {result.get("error", "Unknown")}', 'error')
    
    except Exception as e:
        flash(f'Ошибка запуска сбора: {str(e)}', 'error')
    
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
        # Инициализируем БД если не существует  
        from .database import init_database, test_db
        if not test_db():
            print("⚡ Инициализация БД в health check...")
            init_database()
            
        # Проверяем доступность базы данных
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM channels')
        channels_count = cursor.fetchone()[0]
        conn.close()
        
        # Получаем информацию о последнем запуске
        try:
            recent_logs = get_run_logs(1)
            last_run = recent_logs[0] if recent_logs else None
        except:
            last_run = None
        
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'channels_count': channels_count,
            'last_run': last_run['started_at'] if last_run else None,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"❌ Health check error: {error_details}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        }), 500

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