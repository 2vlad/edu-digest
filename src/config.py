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

# База данных
# На Railway используем volume для постоянного хранения
if os.getenv('RAILWAY_ENVIRONMENT'):
    print("🚄 Railway environment detected")
    # Пробуем создать /data, если не получается - используем /tmp
    try:
        print("🔍 Attempting to create /data directory...")
        os.makedirs('/data', exist_ok=True)
        print("✅ /data directory created/exists")
        
        # Проверяем права на запись
        print("✍️ Testing write permissions to /data...")
        test_file = '/data/.write_test'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        DATABASE_PATH = '/data/edu_digest.db'
        print(f"🗄️ ✅ Using /data for persistent storage: {DATABASE_PATH}")
    except (PermissionError, OSError) as e:
        print(f"⚠️ No access to /data ({e}), falling back to /tmp")
        DATABASE_PATH = '/tmp/edu_digest.db'
        print(f"📁 Using temporary storage: {DATABASE_PATH}")
else:
    # Локальная разработка
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'edu_digest.db')
    print(f"🏠 Local development mode: {DATABASE_PATH}")

# Настройки по умолчанию
DEFAULT_MAX_NEWS_COUNT = 10
SCHEDULE_TIMES = ['12:00', '18:00']  # Время публикации дайджестов

# Flask настройки
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_PORT = int(os.getenv('PORT', 5002))