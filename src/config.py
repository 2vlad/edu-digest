import os
import logging
from dotenv import load_dotenv

# Настройка детального логирования
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/config.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Loading EdTech News Digest configuration (Supabase Only)...")

# Загружаем переменные окружения
env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env')
logger.debug(f"📁 Looking for .env file at: {env_file_path}")

if os.path.exists(env_file_path):
    logger.info("✅ .env file found, loading variables")
    load_dotenv()
else:
    logger.info("ℹ️ No .env file found, using system environment variables only")
    load_dotenv()

# Определяем среду выполнения
environment = os.getenv('RAILWAY_ENVIRONMENT', 'local')
logger.info(f"🌍 Environment: {environment}")

# Telegram API настройки
logger.info("🔧 Loading Telegram API configuration...")
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', '@vestnik_edtech')

# Логируем статус Telegram переменных
logger.debug("📱 Telegram API variables:")
logger.debug(f"   TELEGRAM_API_ID: {'✅ Set' if TELEGRAM_API_ID else '❌ Missing'}")
logger.debug(f"   TELEGRAM_API_HASH: {'✅ Set' if TELEGRAM_API_HASH else '❌ Missing'}")
logger.debug(f"   TELEGRAM_BOT_TOKEN: {'✅ Set' if TELEGRAM_BOT_TOKEN else '❌ Missing'}")
logger.debug(f"   TARGET_CHANNEL: {TARGET_CHANNEL}")

if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
    logger.error("❌ Telegram API credentials missing")
    logger.error("💡 Get credentials from https://my.telegram.org/auth")
    logger.error("💡 Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env file")
    
if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ Telegram Bot Token missing")
    logger.error("💡 Get bot token from @BotFather")
    logger.error("💡 Set TELEGRAM_BOT_TOKEN in .env file")

# Claude API настройки
logger.info("🤖 Loading Claude AI API configuration...")
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
logger.debug(f"   ANTHROPIC_API_KEY: {'✅ Set' if ANTHROPIC_API_KEY else '❌ Missing'}")

if not ANTHROPIC_API_KEY:
    logger.error("❌ Claude API key missing")
    logger.error("💡 Get API key from https://console.anthropic.com/")
    logger.error("💡 Set ANTHROPIC_API_KEY in .env file")

# Supabase настройки (ОБЯЗАТЕЛЬНЫЕ)
logger.info("🐘 Loading Supabase configuration...")
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')  # Anon/Public API Key
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Service Role Key (опционально)
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string

# Логируем статус Supabase переменных  
logger.debug("🗄️ Supabase configuration:")
logger.debug(f"   DATABASE_URL: {'✅ Set' if DATABASE_URL else '❌ Missing'}")
logger.debug(f"   SUPABASE_URL: {'✅ Set' if SUPABASE_URL else '❌ Missing'}")
logger.debug(f"   SUPABASE_ANON_KEY: {'✅ Set' if SUPABASE_KEY else '❌ Missing'}")
logger.debug(f"   SUPABASE_SERVICE_KEY: {'✅ Set' if SUPABASE_SERVICE_KEY else '❌ Missing'}")

# Проверяем обязательные переменные
missing_vars = []
if not DATABASE_URL:
    missing_vars.append('DATABASE_URL')
if not SUPABASE_URL:
    missing_vars.append('SUPABASE_URL')
if not SUPABASE_KEY:
    missing_vars.append('SUPABASE_ANON_KEY')

if missing_vars:
    logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют обязательные переменные Supabase:")
    for var in missing_vars:
        logger.error(f"   - {var}")
    logger.error("💡 Настройте Supabase проект и добавьте переменные в .env файл")
    raise ValueError(f"Missing required Supabase variables: {', '.join(missing_vars)}")

# Безопасно показываем DATABASE_URL (скрываем пароль)
if DATABASE_URL:
    safe_db_url = DATABASE_URL[:20] + "***" + DATABASE_URL[-20:] if len(DATABASE_URL) > 40 else "***"
    logger.info(f"✅ PostgreSQL connection configured: {safe_db_url}")

logger.info(f"✅ Supabase project: {SUPABASE_URL}")

# Генерируем сводку конфигурации
logger.info("📋 Configuration Summary:")
logger.info("=" * 40)
logger.info(f"🌍 Environment: {environment}")
logger.info(f"📱 Telegram API: {'✅ Ready' if TELEGRAM_API_ID and TELEGRAM_API_HASH else '❌ Missing credentials'}")
logger.info(f"🤖 Claude AI: {'✅ Ready' if ANTHROPIC_API_KEY else '❌ Missing API key'}")
logger.info(f"🐘 Supabase Database: ✅ Configured")
logger.info(f"🎯 Target Channel: {TARGET_CHANNEL}")
logger.info("=" * 40)

# Настройки по умолчанию
DEFAULT_MAX_NEWS_COUNT = 10
SCHEDULE_TIMES = ['12:00', '18:00']  # Время публикации дайджестов

# Flask настройки
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_PORT = int(os.getenv('PORT', 5002))