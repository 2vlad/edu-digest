import os
import logging
from dotenv import load_dotenv

# Настройка детального логирования для конфигурации
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/config.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Loading EdTech News Digest configuration...")

# Загружаем переменные окружения
env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env')
logger.debug(f"📁 Looking for .env file at: {env_file_path}")

if os.path.exists(env_file_path):
    logger.info("✅ .env file found, loading variables")
    load_dotenv()
else:
    logger.info("ℹ️ No .env file found, using system environment variables only")
    load_dotenv()  # Still call to load from system env

# Определяем среду выполнения
environment = os.getenv('RAILWAY_ENVIRONMENT', 'local')
logger.info(f"🌍 Environment: {environment}")
logger.debug(f"🐍 Python working directory: {os.getcwd()}")

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
    logger.warning("⚠️ Telegram API credentials missing - real channel reading will fail")
    logger.warning("💡 Get credentials from https://my.telegram.org/auth")
    
if not TELEGRAM_BOT_TOKEN:
    logger.warning("⚠️ Telegram Bot Token missing - publishing will fail")
    logger.warning("💡 Get bot token from @BotFather")

# Claude API настройки
logger.info("🤖 Loading Claude AI API configuration...")
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
logger.debug(f"   ANTHROPIC_API_KEY: {'✅ Set' if ANTHROPIC_API_KEY else '❌ Missing'}")

if not ANTHROPIC_API_KEY:
    logger.warning("⚠️ Claude API key missing - AI summarization will fail")
    logger.warning("💡 Get API key from https://console.anthropic.com/")

# База данных - Supabase (PostgreSQL)
logger.info("🐘 Loading Supabase/PostgreSQL configuration...")
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')  # Anon/Public API Key
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Service Role Key (опционально)
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string

# Логируем статус Database переменных  
logger.debug("🗄️ Database configuration:")
logger.debug(f"   DATABASE_URL: {'✅ Set' if DATABASE_URL else '❌ Missing'}")
logger.debug(f"   SUPABASE_URL: {'✅ Set' if SUPABASE_URL else '❌ Missing'}")
logger.debug(f"   SUPABASE_ANON_KEY: {'✅ Set' if SUPABASE_KEY else '❌ Missing'}")
logger.debug(f"   SUPABASE_SERVICE_KEY: {'✅ Set' if SUPABASE_SERVICE_KEY else '❌ Missing'}")

if DATABASE_URL:
    # Безопасно показываем DATABASE_URL (скрываем пароль)
    safe_db_url = DATABASE_URL[:20] + "***" + DATABASE_URL[-20:] if len(DATABASE_URL) > 40 else "***"
    logger.info(f"✅ PostgreSQL connection string configured: {safe_db_url}")
else:
    logger.warning("⚠️ DATABASE_URL missing - PostgreSQL connection will fail")

# Валидация Supabase конфигурации
def validate_supabase_config():
    """Проверяем корректность настроек Supabase"""
    logger.debug("🔍 Validating Supabase configuration...")
    
    if SUPABASE_URL and not SUPABASE_KEY:
        logger.error("❌ Configuration Error: SUPABASE_URL specified but SUPABASE_ANON_KEY missing")
        logger.error("💡 Both SUPABASE_URL and SUPABASE_ANON_KEY are required together")
        return False
        
    if SUPABASE_KEY and not SUPABASE_URL:
        logger.error("❌ Configuration Error: SUPABASE_ANON_KEY specified but SUPABASE_URL missing")
        logger.error("💡 Both SUPABASE_URL and SUPABASE_ANON_KEY are required together")
        return False
        
    if SUPABASE_URL and SUPABASE_KEY:
        logger.info("✅ Supabase configuration is valid")
        return True
        
    logger.info("ℹ️ No Supabase configuration found")
    return True  # Не ошибка, просто не используем Supabase

# Функция для генерации SQLite пути (используется и для fallback)
def get_sqlite_path():
    """Определяет путь к SQLite базе данных для fallback"""
    logger.debug("📁 Determining SQLite database path...")
    
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.debug("🚂 Railway environment detected")
        try:
            logger.debug("🗂️ Attempting to create /data directory...")
            os.makedirs('/data', exist_ok=True)
            
            # Проверяем права на запись
            test_file = '/data/.write_test'
            logger.debug(f"✏️ Testing write permissions: {test_file}")
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            sqlite_path = '/data/edu_digest.db'
            logger.info(f"✅ SQLite path (Railway persistent): {sqlite_path}")
            return sqlite_path
            
        except (PermissionError, OSError) as e:
            logger.warning(f"⚠️ Cannot write to /data directory: {e}")
            sqlite_path = '/tmp/edu_digest.db'
            logger.warning(f"🔄 Using temporary path: {sqlite_path}")
            return sqlite_path
    else:
        # Локальная разработка
        logger.debug("🏠 Local development environment")
        local_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        try:
            logger.debug(f"🗂️ Creating local data directory: {local_data_dir}")
            os.makedirs(local_data_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ Cannot create local data directory: {e}")
            
        sqlite_path = os.path.join(local_data_dir, 'edu_digest.db')
        logger.info(f"✅ SQLite path (local): {sqlite_path}")
        return sqlite_path

# Определяем DATABASE_PATH - всегда должен быть доступен для fallback
logger.info("🔧 Setting up database paths...")
DATABASE_PATH = get_sqlite_path()

# Определяем основной тип базы данных
logger.info("🎯 Determining primary database configuration...")

config_valid = validate_supabase_config()
has_postgres = DATABASE_URL or SUPABASE_URL

if not config_valid or not has_postgres:
    if not config_valid:
        logger.warning("⚠️ Invalid Supabase configuration detected")
    else:
        logger.info("ℹ️ No PostgreSQL configuration found")
    
    logger.warning("🔄 System will attempt Supabase connection but may fallback to SQLite")
    logger.info(f"📁 SQLite fallback path: {DATABASE_PATH}")
else:
    primary_db = SUPABASE_URL or "Direct PostgreSQL connection"
    logger.info(f"✅ Primary database: PostgreSQL ({primary_db})")
    logger.info(f"🔄 SQLite fallback available at: {DATABASE_PATH}")

# Генерируем сводку конфигурации
logger.info("📋 Configuration Summary:")
logger.info("=" * 40)
logger.info(f"🌍 Environment: {environment}")
logger.info(f"📱 Telegram API: {'✅ Ready' if TELEGRAM_API_ID and TELEGRAM_API_HASH else '❌ Missing credentials'}")
logger.info(f"🤖 Claude AI: {'✅ Ready' if ANTHROPIC_API_KEY else '❌ Missing API key'}")
logger.info(f"🐘 PostgreSQL: {'✅ Configured' if has_postgres else '❌ Not configured'}")
logger.info(f"📁 SQLite Fallback: ✅ Available at {DATABASE_PATH}")
logger.info(f"🎯 Target Channel: {TARGET_CHANNEL}")
logger.info("=" * 40)

# Настройки по умолчанию
DEFAULT_MAX_NEWS_COUNT = 10
SCHEDULE_TIMES = ['12:00', '18:00']  # Время публикации дайджестов

# Flask настройки
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
FLASK_PORT = int(os.getenv('PORT', 5002))