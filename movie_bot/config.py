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
DB_PATH = BASE_DIR / "data" / "movies.db"

# Создаём папки
LOGS_DIR.mkdir(exist_ok=True)
DB_PATH.parent.mkdir(exist_ok=True)