import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API настройки
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '@vestnik_edtech')

# Claude API настройки
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# База данных - Supabase (PostgreSQL)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')  # Anon/Public API Key
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Service Role Key (опционально)
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string

# Валидация Supabase конфигурации
def validate_supabase_config():
    """Проверяем корректность настроек Supabase"""
    if SUPABASE_URL and not SUPABASE_KEY:
        print("❌ Ошибка: SUPABASE_URL указан, но отсутствует SUPABASE_ANON_KEY")
        return False
    if SUPABASE_KEY and not SUPABASE_URL:
        print("❌ Ошибка: SUPABASE_ANON_KEY указан, но отсутствует SUPABASE_URL")
        return False
    return True

# Поддержка старого SQLite для локальной разработки (fallback)
if not validate_supabase_config() or (not DATABASE_URL and not SUPABASE_URL):
    if not validate_supabase_config():
        print("⚠️ Неправильная конфигурация Supabase, используем SQLite fallback")
    else:
        print("⚠️ Supabase не настроен, используем SQLite fallback")
    if os.getenv('RAILWAY_ENVIRONMENT'):
        print("🚄 Railway environment detected")
        try:
            print("🔍 Attempting to create /data directory...")
            os.makedirs('/data', exist_ok=True)
            test_file = '/data/.write_test'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            DATABASE_PATH = '/data/edu_digest.db'
            print(f"🗄️ Using SQLite at: {DATABASE_PATH}")
        except (PermissionError, OSError) as e:
            DATABASE_PATH = '/tmp/edu_digest.db'
            print(f"📁 Using temporary SQLite: {DATABASE_PATH}")
    else:
        DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'edu_digest.db')
        print(f"🏠 Local SQLite: {DATABASE_PATH}")
else:
    print(f"🐘 Using PostgreSQL: {SUPABASE_URL or 'Direct connection'}")
    DATABASE_PATH = None  # Не используем SQLite

# Настройки по умолчанию
DEFAULT_MAX_NEWS_COUNT = 10
SCHEDULE_TIMES = ['12:00', '18:00']  # Время публикации дайджестов

# Flask настройки
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_PORT = int(os.getenv('PORT', 5002))