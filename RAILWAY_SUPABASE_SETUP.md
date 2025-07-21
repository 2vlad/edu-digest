# Railway + Supabase Setup Guide

## 🚀 Полная инструкция по настройке EdTech News Bot

### 1. Настройка Supabase

1. **Создать проект в Supabase:**
   - Перейти на https://supabase.com
   - Создать новый проект
   - Дождаться инициализации (2-3 минуты)

2. **Получить ключи подключения:**
   - В Dashboard проекта перейти в **Settings** → **API**
   - Скопировать:
     - `Project URL` (например: `https://abcdefgh.supabase.co`)
     - `anon public` ключ (длинный токен)
   - В **Settings** → **Database** найти:
     - `Connection string` для прямого подключения к PostgreSQL

### 2. Настройка Railway

1. **Создать сервис в Railway:**
   - Подключить GitHub репозиторий
   - Выбрать основную ветку

2. **Добавить переменные окружения в Railway:**
   
   **Обязательные для Supabase:**
   ```
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   SUPABASE_URL=https://[PROJECT-REF].supabase.co  
   SUPABASE_ANON_KEY=[ANON-PUBLIC-KEY]
   ```

   **API ключи для ботов:**
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_BOT_TOKEN=your_bot_token
   ANTHROPIC_API_KEY=your_claude_key
   ```

   **Дополнительные настройки:**
   ```
   FLASK_PORT=8080
   RAILWAY_ENVIRONMENT=production
   ```

### 3. Автоматическая настройка базы данных

После деплоя в Railway выполнить:

```bash
# В Railway консоли или через Railway CLI
python direct_supabase_setup.py
```

Этот скрипт:
- ✅ Создаст все необходимые таблицы в Supabase
- ✅ Добавит настройки по умолчанию  
- ✅ Загрузит 10 популярных EdTech каналов
- ✅ Проверит корректность настройки

### 4. Проверка подключения

Для диагностики проблем:

```bash
python test_supabase_connection.py
```

### 5. Настройка Railway Build & Start

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python -m src
```

### 6. Структура таблиц в Supabase

После выполнения `direct_supabase_setup.py` будут созданы:

**channels** - отслеживаемые каналы:
```sql
id (SERIAL PRIMARY KEY)
username (TEXT UNIQUE) - @channel_name
display_name (TEXT) - Отображаемое имя
priority (INTEGER 0-10) - Приоритет
is_active (BOOLEAN) - Активен ли канал
last_message_id (BIGINT) - ID последнего обработанного сообщения
created_at, updated_at (TIMESTAMP)
```

**processed_messages** - обработанные сообщения:
```sql  
id (SERIAL PRIMARY KEY)
channel_id (INTEGER) - Ссылка на channels
message_id (BIGINT) - ID сообщения Telegram
message_text (TEXT) - Текст сообщения
summary (TEXT) - Саммаризация через Claude
processed_at (TIMESTAMP)
published (BOOLEAN) - Опубликовано в дайджесте
```

**settings** - настройки системы:
```sql
id (SERIAL PRIMARY KEY)  
key (TEXT UNIQUE) - Ключ настройки
value (TEXT) - Значение
description (TEXT) - Описание
created_at, updated_at (TIMESTAMP)
```

**run_logs** - логи запусков:
```sql
id (SERIAL PRIMARY KEY)
started_at, completed_at (TIMESTAMP) 
status (TEXT) - started/completed/failed
channels_processed (INTEGER)
messages_collected (INTEGER)  
news_published (INTEGER)
error_message (TEXT)
```

### 7. Готовые EdTech каналы

Автоматически добавляются:
- @edtexno (EdTechno) - приоритет 10
- @vc_edtech (VC EdTech) - приоритет 9
- @rusedweek (Russian EdWeek) - приоритет 8
- @edtech_hub (EdTech Hub) - приоритет 8
- @prosv_media (Просвещение Медиа) - приоритет 7
- @digitaleducation (Цифровое образование) - приоритет 7
- @skillfactory_news (SkillFactory News) - приоритет 6
- @netology_ru (Нетология) - приоритет 6  
- @geekbrains_ru (GeekBrains) - приоритет 6
- @skyengschool (Skyeng) - приоритет 5

### 8. Диагностика проблем

**Ошибка "Network is unreachable":**
- Проверить корректность `DATABASE_URL`
- Убедиться что Supabase проект активен
- Проверить сетевые ограничения Railway

**Пустая база данных:**
- Выполнить `python direct_supabase_setup.py` 
- Проверить переменные окружения
- Проверить логи Railway деплоя

**Ошибки подключения к Telegram:**
- Проверить `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`
- Убедиться что `TELEGRAM_BOT_TOKEN` валиден
- Проверить что бот добавлен в целевой канал

### 9. Мониторинг

После настройки:
- Админ-панель: `https://[railway-url].railway.app`
- Endpoint здоровья: `https://[railway-url].railway.app/health`
- API статистики: `https://[railway-url].railway.app/api/stats`

### 10. Ручная настройка (если автоскрипт не работает)

Если `direct_supabase_setup.py` не сработал, можно создать таблицы вручную в Supabase Dashboard → SQL Editor:

```sql
-- Создать все таблицы одним запросом  
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    priority INTEGER DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
    is_active BOOLEAN DEFAULT true,
    last_message_id BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processed_messages (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    message_id BIGINT NOT NULL,
    message_text TEXT,
    summary TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published BOOLEAN DEFAULT false,
    UNIQUE(channel_id, message_id)
);

CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS run_logs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT CHECK (status IN ('started', 'completed', 'failed')),
    channels_processed INTEGER DEFAULT 0,
    messages_collected INTEGER DEFAULT 0,
    news_published INTEGER DEFAULT 0,
    error_message TEXT
);

-- Добавить настройки по умолчанию
INSERT INTO settings (key, value, description) VALUES 
('max_news_count', '10', 'Максимальное количество новостей в дайджесте'),
('target_channel', '@vestnik_edtech', 'Целевой канал для публикации'),
('digest_times', '12:00,18:00', 'Время публикации дайджестов'),
('summary_max_length', '150', 'Максимальная длина суммаризации в символах'),
('hours_lookback', '12', 'Сколько часов назад искать новости')
ON CONFLICT (key) DO NOTHING;
```

---

## ✅ После выполнения всех шагов

Система будет полностью готова:
- 🐘 PostgreSQL база данных в Supabase
- 📺 10 EdTech каналов добавлены
- ⚙️ Настройки системы применены  
- 🤖 Flask админ-панель доступна
- 🚀 Готово к сбору новостей и публикации дайджестов

**Следующий шаг:** Откройте админ-панель и нажмите "Запустить сбор новостей" для тестирования системы.