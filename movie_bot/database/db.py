"""
Модуль управления подключением к базе данных SQLite.

Функции:
- Инициализация БД при старте
- Контекстный менеджер `get_db()` для безопасного доступа
- Автоматическое обновление схемы (добавление колонок)
"""

import aiosqlite
import logging
from contextlib import asynccontextmanager

DB_NAME = "movies.db"
logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_db():
    """
     Контекстный менеджер для подключения к SQLite.

    Пример:
        async with get_db() as db:
            await db.execute("SELECT * FROM movies")
    """
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    """
    Инициализирует базу данных: создаёт таблицу `movies` и добавляет новые колонки при необходимости.

    Автоматически:
    - Создаёт таблицу, если не существует
    - Удаляет устаревшую колонку `watch_later`
    - Добавляет колонку `watched`, если её нет

    Логгирует ход инициализации.
    """
    async with get_db() as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                description TEXT,
                poster_id TEXT,
                added_at TEXT DEFAULT (datetime('now', 'localtime')),
                watched INTEGER DEFAULT 0
            )
            """
        )
        async with db.execute("PRAGMA table_info(movies)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
        if "watch_later" in columns:
            await db.execute("ALTER TABLE movies DROP COLUMN watch_later")
        if "watched" not in columns:
            await db.execute("ALTER TABLE movies ADD COLUMN watched INTEGER DEFAULT 0")
        await db.commit()
        logger.info("База данных инициализирована")