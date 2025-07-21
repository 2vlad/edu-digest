# EdTech News Digest Bot

Автоматический бот для сбора и публикации дайджеста новостей по образовательным технологиям из Telegram каналов.

## Возможности

- 🤖 Автоматический сбор новостей из Telegram каналов
- 📝 Суммаризация публикаций с помощью Claude AI
- ⏰ Публикация дайджестов дважды в день (12:00 и 18:00) 
- 🎯 Система приоритетов для каналов (0-10)
- 🌐 Веб-админ-панель для управления
- 📊 Система логирования и мониторинга
- 🚀 Готов к деплою на Railway

## Деплой на Railway

### Автоматический деплой (рекомендуется)

1. **Форк проекта** на GitHub
2. **Подключите к Railway:**
   ```bash
   # Зайдите на railway.app
   # Создайте новый проект
   # Подключите ваш GitHub репозиторий
   ```

3. **Настройте переменные окружения в Railway:**
   ```
   TELEGRAM_API_ID=your_telegram_api_id
   TELEGRAM_API_HASH=your_telegram_api_hash  
   TELEGRAM_BOT_TOKEN=your_bot_token
   TARGET_CHANNEL=@your_target_channel
   ANTHROPIC_API_KEY=your_claude_api_key
   FLASK_SECRET_KEY=your_secret_key
   PORT=5000
   ```

4. **Деплой произойдет автоматически** через GitHub Actions

### Ручной деплой

```bash
# Установите Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Войдите в аккаунт
railway login

# Деплой
railway up
```

## Локальная разработка

### Установка

```bash
git clone https://github.com/yourusername/edu-digest
cd edu-digest
pip install -r requirements.txt
```

### Настройка

```bash
# Скопируйте шаблон конфигурации
cp .env.example .env

# Отредактируйте .env файл с вашими API ключами
```

### Запуск

```bash
# Инициализация базы данных
python init_db.py

# Сбор новостей (однократно)
python main.py collect

# Запуск админ-панели
python main.py admin

# Запуск планировщика
python scheduler.py
```
- 🌐 Web админ-панель для управления каналами
- 🚀 Готов для деплоя на Railway

## Технологический стек

- **Python 3.9+**
- **SQLite** - база данных
- **Flask** - админ-панель
- **Telethon** - работа с Telegram API
- **Claude API** - суммаризация текстов
- **Railway** - деплой

## Быстрый запуск

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Настройте переменные окружения в `.env`
4. Запустите сбор новостей: `python main.py collect`
5. Запустите админ-панель: `python main.py admin`

## Конфигурация

Переименуйте `.env.example` в `.env` и заполните:

```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
ANTHROPIC_API_KEY=your_claude_key
TARGET_CHANNEL=@your_channel
```

## Структура проекта

```
edu-digest/
├── src/                 # Исходный код
│   ├── config.py       # Конфигурация
│   └── __init__.py
├── data/               # База данных SQLite
├── logs/              # Логи работы
├── main.py            # Точка входа
├── requirements.txt   # Зависимости Python
└── Procfile          # Конфигурация Railway
```

## Разработка

Проект находится в разработке. Реализованные модули:
- [x] Task 1: Базовая структура проекта
- [ ] Task 2: База данных SQLite
- [ ] Task 3: Интеграция с Telegram API
- [ ] Task 4: Интеграция с Claude API
- [ ] Task 5: Модуль сбора новостей
- [ ] Task 6: Flask админ-панель
- [ ] Task 7: Система настроек
- [ ] Task 8: Публикация дайджестов
- [ ] Task 9: Логирование и мониторинг
- [ ] Task 10: Автоматизация и деплой