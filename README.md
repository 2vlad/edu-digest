# EdTech News Digest Bot

Автоматический бот для сбора, суммаризации и публикации новостей из сферы образовательных технологий (EdTech).

## 🚀 Возможности

- **Сбор новостей** из Telegram каналов с помощью Telethon API
- **Умная суммаризация** новостей с помощью Claude AI
- **Фильтрация и приоритизация** контента по релевантности
- **Автоматическая публикация** дайджестов в Telegram канал
- **Веб-интерфейс** для управления каналами и настройками
- **PostgreSQL база данных** через Supabase для надежного хранения

## 🏗️ Архитектура

- **Python + Flask** для веб-интерфейса
- **Supabase (PostgreSQL)** для базы данных
- **Telethon** для работы с Telegram API
- **Claude AI** для суммаризации новостей
- **Готовность к деплою** на Railway

## 📋 Требования

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Supabase (обязательно)
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://user:password@host:port/database

# Telegram API (получить на https://my.telegram.org/auth)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TARGET_CHANNEL=@your_channel

# Claude AI (получить на https://console.anthropic.com/)
ANTHROPIC_API_KEY=your_claude_api_key

# Flask
FLASK_SECRET_KEY=your_secret_key_for_production
PORT=5002
```

### Зависимости

```bash
pip install -r requirements.txt
```

## 🚀 Быстрый старт

### 1. Настройка Supabase

1. Создайте проект на [supabase.com](https://supabase.com)
2. Получите `SUPABASE_URL` и `SUPABASE_ANON_KEY` из настроек проекта
3. Получите `DATABASE_URL` из раздела Settings → Database

### 2. Инициализация

```bash
# Установка зависимостей
pip install -r requirements.txt

# Инициализация базы данных
python main.py init
```

### 3. Запуск

```bash
# Админ-панель (управление каналами и настройками)
python main.py admin

# Сбор и публикация новостей
python main.py collect
```

## 🌐 Веб-интерфейс

Админ-панель доступна по адресу: `http://localhost:5002`

### Функции:
- **Дашборд** - статистика и обзор системы
- **Каналы** - управление отслеживаемыми Telegram каналами
- **Настройки** - конфигурация параметров сбора и публикации
- **Логи** - просмотр истории запусков

## 📊 Структура базы данных

- `channels` - отслеживаемые Telegram каналы
- `processed_messages` - обработанные сообщения (для избежания дублей)
- `settings` - настройки системы
- `run_logs` - логи запусков сбора новостей

## 🔧 Команды

```bash
python main.py collect  # Сбор и публикация новостей
python main.py admin    # Запуск веб-интерфейса
python main.py init     # Инициализация базы данных
```

## 🚢 Деплой на Railway

1. Подключите репозиторий к Railway
2. Настройте переменные окружения в Railway Dashboard
3. Добавьте Supabase addon или используйте внешний проект
4. Деплой произойдет автоматически

### Railway конфигурация

`Procfile`:
```
web: python main.py admin
worker: python main.py collect
```

`railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE"
  }
}
```

## 📈 Мониторинг

- **Health check**: `GET /health` - статус системы
- **Логирование** во все модули с ротацией файлов
- **Статистика** в веб-интерфейсе

## 🔐 Безопасность

- Все чувствительные данные в переменных окружения
- Автоматическая валидация входных данных
- Защищенные SQL-запросы через параметризацию

## 🛠️ Разработка

### Структура проекта:
```
├── src/
│   ├── config.py           # Конфигурация
│   ├── database.py         # Работа с Supabase
│   ├── news_collector.py   # Основная логика сбора
│   ├── claude_summarizer.py # Суммаризация через Claude
│   ├── telegram_bot.py     # Публикация в Telegram
│   ├── telegram_client.py  # Чтение из Telegram
│   └── admin_panel.py      # Веб-интерфейс
├── templates/              # HTML шаблоны
├── main.py                 # Точка входа
├── init_supabase.py       # Инициализация БД
└── requirements.txt        # Зависимости
```

### Логирование:
- `logs/main.log` - основные операции
- `logs/database.log` - операции с БД
- `logs/news_collector.log` - сбор новостей
- `logs/admin.log` - веб-интерфейс

## 📝 Лицензия

MIT License

## 🤝 Поддержка

При возникновении вопросов проверьте:
1. Правильность переменных окружения
2. Доступность Supabase проекта
3. Валидность API ключей Telegram и Claude
4. Логи в папке `logs/` 