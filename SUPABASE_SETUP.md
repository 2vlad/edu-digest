# Настройка Supabase для EdTech News Digest Bot

## 1. Создание проекта в Supabase

1. Перейдите на https://supabase.com
2. Создайте новый проект
3. Выберите регион (желательно ближайший к вашему Railway серверу)
4. Дождитесь создания проекта (1-2 минуты)

## 2. Получение настроек подключения

В панели Supabase:

### Settings → API
- `SUPABASE_URL` - Project URL (например: `https://your-project.supabase.co`)  
- `SUPABASE_ANON_KEY` - anon public key

### Settings → Database
- `DATABASE_URL` - Connection string для прямого подключения к PostgreSQL
  - Формат: `postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT].supabase.co:5432/postgres`

## 3. Переменные окружения для Railway

В Railway добавьте следующие переменные:

```bash
# Supabase настройки
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres

# Существующие переменные Telegram и Claude
TELEGRAM_API_ID=your-api-id
TELEGRAM_API_HASH=your-api-hash
TELEGRAM_BOT_TOKEN=your-bot-token
ANTHROPIC_API_KEY=your-claude-key

# Flask настройки
FLASK_SECRET_KEY=your-secret-key
```

## 4. Локальная разработка

Создайте файл `.env` в корне проекта:

```env
# Supabase настройки
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres

# Остальные настройки...
TELEGRAM_API_ID=your-api-id
TELEGRAM_API_HASH=your-api-hash
TELEGRAM_BOT_TOKEN=your-bot-token
ANTHROPIC_API_KEY=your-claude-key
```

## 5. Автоматическое создание таблиц

Таблицы создаются автоматически при первом запуске приложения:
- `channels` - отслеживаемые каналы
- `processed_messages` - обработанные сообщения
- `settings` - настройки системы
- `run_logs` - логи запусков

## 6. Проверка работы

После настройки переменных окружения:

1. **Railway**: деплой автоматически создаст таблицы при первом запуске
2. **Локально**: запустите `python -m src` и проверьте логи

## 7. Fallback на SQLite

Если Supabase не настроен, система автоматически использует SQLite:
- **Локально**: `data/edu_digest.db`
- **Railway**: попытается использовать `/data/edu_digest.db` или `/tmp/edu_digest.db`

## 8. Миграция данных (если нужно)

Если у вас уже есть данные в SQLite, вы можете их экспортировать:

```python
# Экспорт из SQLite в CSV
import sqlite3
import csv

conn = sqlite3.connect('data/edu_digest.db')
cursor = conn.cursor()

# Экспорт каналов
cursor.execute('SELECT * FROM channels')
with open('channels.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'username', 'display_name', 'priority', 'is_active', 'last_message_id', 'created_at', 'updated_at'])
    writer.writerows(cursor.fetchall())
```

Затем импортировать в Supabase через веб-интерфейс или SQL.

## 9. Преимущества Supabase

✅ **Персистентность**: данные сохраняются между деплоями  
✅ **Масштабируемость**: PostgreSQL хорошо работает под нагрузкой  
✅ **Railway совместимость**: нет проблем с файловой системой  
✅ **Веб-интерфейс**: удобное управление данными  
✅ **Бэкапы**: автоматическое резервное копирование  
✅ **Real-time**: возможность добавить реальные обновления  

## 10. Мониторинг

- В Supabase Dashboard можете отслеживать использование БД
- В Railway смотрите логи приложения
- Health check endpoint `/health` покажет статус подключения к БД