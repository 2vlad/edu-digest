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
# На Railway используем /tmp временно до настройки volume
if os.getenv('RAILWAY_ENVIRONMENT'):
    DATABASE_PATH = '/tmp/edu_digest.db'
else:
    # Локальная разработка
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'edu_digest.db')

# Настройки по умолчанию
DEFAULT_MAX_NEWS_COUNT = 10
SCHEDULE_TIMES = ['12:00', '18:00']  # Время публикации дайджестов

# Flask настройки
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_PORT = int(os.getenv('PORT', 5002))