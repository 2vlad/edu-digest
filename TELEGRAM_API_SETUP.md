# Настройка Telegram API для реальных данных

## 🚨 ПРОБЛЕМА: Публикуются тестовые дайджесты

**Причина:** Система не может подключиться к реальным Telegram каналам и переключается на тестовые данные.

**Решение:** Правильно настроить Telegram API credentials в Railway.

---

## 🔑 Шаг 1: Получение Telegram API Credentials

### 1.1. Регистрация приложения

1. Перейти на https://my.telegram.org/auth
2. Войти с помощью номера телефона (тот же аккаунт, который будет читать каналы)
3. Выбрать **"API development tools"**
4. Заполнить форму создания приложения:
   - **App title:** `EdTech News Digest Bot`
   - **Short name:** `edu_digest`
   - **Platform:** `Server`
   - **Description:** `Educational technology news aggregation bot`

### 1.2. Получение ключей

После создания приложения вы получите:
- **api_id** - числовой ID (например: `12345678`)
- **api_hash** - строковый хэш (например: `abcdef123456789...`)

**⚠️ ВАЖНО:** Сохраните эти данные - они понадобятся для Railway.

---

## 🔧 Шаг 2: Создание Telegram Bot

### 2.1. Создание через BotFather

1. Найти @BotFather в Telegram
2. Отправить команду `/newbot`
3. Выбрать имя бота: `EdTech News Digest`
4. Выбрать username: `edu_digest_news_bot` (должен заканчиваться на `_bot`)

### 2.2. Получение Bot Token

BotFather выдаст токен вида: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

**⚠️ ВАЖНО:** Сохраните токен - он понадобится для Railway.

---

## 🚢 Шаг 3: Настройка Railway Environment Variables

Добавить в Railway Dashboard → Environment Variables:

```env
# Telegram User API (для чтения каналов)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef123456789abcdef123456789ab

# Telegram Bot API (для публикации дайджестов)  
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

## 🧪 Шаг 4: Тестирование подключения

После деплоя в Railway выполнить:

```bash
python test_telegram_api.py
```

**Ожидаемый результат:**
```
✅ Telethon User API connection successful
✅ Successfully read 3 messages from @edtexno
✅ Bot API connection successful
```

**Если ошибки:**
```
❌ CRITICAL ERROR: Missing Telegram API credentials
❌ Telethon User API connection failed
❌ Bot API connection failed
```

---

## 🔍 Диагностика проблем

### Проблема: "Missing Telegram API credentials"

**Решение:**
1. Проверить что переменные добавлены в Railway
2. Перезапустить Railway service
3. Проверить что нет опечаток в названиях переменных

### Проблема: "Telethon User API connection failed"

**Возможные причины:**
1. **Неверные api_id/api_hash** - проверить на https://my.telegram.org
2. **Аккаунт требует авторизации** - нужна первоначальная авторизация
3. **Заблокированный аккаунт** - проверить доступ к Telegram
4. **Сетевые проблемы** - Railway не может подключиться к Telegram

**Решение для авторизации:**
```bash
# Локально выполнить один раз для авторизации
cd edu-digest
python -c "
import asyncio
from telethon import TelegramClient
async def auth():
    client = TelegramClient('edu_digest_bot', API_ID, 'API_HASH')
    await client.start()
    print('Authorized!')
asyncio.run(auth())
"
```

### Проблема: "No messages found in channel"

**Возможные причины:**
1. **Канал приватный** - бот не имеет доступа
2. **Канал неактивен** - нет сообщений за последние 24 часа
3. **Неверное имя канала** - проверить @username

---

## 🎯 Шаг 5: Добавление бота в целевой канал

### 5.1. Для публикации дайджестов

1. Перейти в канал `@vestnik_edtech`
2. Добавить бота как администратора
3. Дать права:
   - ✅ Post messages
   - ✅ Edit messages
   - ❌ Delete messages (не обязательно)

### 5.2. Проверка прав

Выполнить тест публикации:
```bash
python -c "
import asyncio
from src.telegram_publisher import TelegramPublisher
async def test():
    pub = TelegramPublisher()
    result = await pub.send_digest_to_channel('TEST: Bot API working!', '@vestnik_edtech')
    print(f'Result: {result}')
asyncio.run(test())
"
```

---

## 🔄 Шаг 6: Проверка результата

После настройки API:

### 6.1. Запустить сбор новостей
1. Открыть админ-панель: `https://[railway-url].railway.app`
2. Нажать **"Запустить сбор новостей"**

### 6.2. Проверить логи
```bash
# В Railway консоли
tail -f logs/telegram_reader.log
tail -f logs/news_collector.log
```

**Ожидаемые логи (успех):**
```
✅ Telethon client authorized successfully
👤 User: Ваше Имя (@ваш_username)
📡 Получено 5 РЕАЛЬНЫХ сообщений из @edtexno
✅ Digest published to @vestnik_edtech
```

**Логи при ошибках:**
```
❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось инициализировать Telegram reader
🚫 SIMULATION IS DISABLED IN PRODUCTION - REAL DATA ONLY!
```

---

## 🎉 Результат

После правильной настройки:
- ❌ **Тестовые дайджесты прекратятся**
- ✅ **Будут публиковаться реальные новости из EdTech каналов**
- ✅ **Система будет работать стабильно без fallback на симуляцию**

---

## 🆘 Если ничего не работает

1. **Проверить Railway Environment Variables** - должны быть установлены все 3 переменные
2. **Перезапустить Railway service** - после добавления переменных
3. **Выполнить тест:** `python test_telegram_api.py`
4. **Проверить логи:** Railway → Logs → ошибки подключения
5. **Создать новое приложение** на https://my.telegram.org если проблемы с API

**Важно:** После исправления система **автоматически** перестанет публиковать тестовые дайджесты и начнет использовать реальные данные!