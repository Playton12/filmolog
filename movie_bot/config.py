"""
Глобальная конфигурация бота.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Основные
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENV = os.getenv("ENV", "dev")

# Пагинация
ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", 5))

# Пути
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"

# На Fly.io данные хранятся на persistent volume /data
# Локально — в ./data/
_IS_FLY = bool(os.getenv("FLY_APP_NAME"))
DB_PATH = Path("/data/movies.db") if _IS_FLY else BASE_DIR / "data" / "movies.db"


def ensure_directories():
    """Создаёт необходимые директории. Вызывать явно, не при импорте."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
