"""
Модуль управления подключением к базе данных SQLite.

Функции:
- Инициализация БД при старте
- Контекстный менеджер `get_db()` для безопасного доступа
- Автоматическое обновление схемы
"""

import aiosqlite
import logging
from contextlib import asynccontextmanager

from movie_bot.config import DB_PATH

logger = logging.getLogger(__name__)
DB_FILE = DB_PATH

# Список разрешённых полей для сортировки (защита от инъекций)
ALLOWED_ORDER_FIELDS = {"id", "title", "genre", "added_at", "watched", "watched_at"}


@asynccontextmanager
async def get_db():
    """
    Контекстный менеджер для подключения к SQLite.
    Устанавливает:
    - Row factory (доступ по имени)
    - WAL-режим (лучшая параллельность)
    - Таймауты
    """
    conn = None
    try:
        conn = await aiosqlite.connect(DB_FILE, timeout=10)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.commit()
        yield conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        raise
    finally:
        if conn:
            await conn.close()


async def init_db():
    """
    Инициализирует базу данных:
    - Создаёт таблицу `movies`
    - Добавляет недостающие колонки
    - Удаляет устаревшую колонку `watch_later`
    - Создаёт необходимые индексы
    """
    async with get_db() as db:
        try:
            # Создаём таблицу
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    description TEXT,
                    poster_id TEXT,
                    added_at TEXT DEFAULT (datetime('now')),
                    watched_at TEXT,
                    watched INTEGER DEFAULT 0,
                    UNIQUE(user_id, title) ON CONFLICT IGNORE
                )
                """
            )

            # Получаем текущие колонки
            async with db.execute("PRAGMA table_info(movies)") as cursor:
                columns = {row[1] for row in await cursor.fetchall()}

            # Удаляем устаревшую колонку
            if "watch_later" in columns:
                try:
                    await db.execute("ALTER TABLE movies DROP COLUMN watch_later")
                    logger.info("Удалена устаревшая колонка: watch_later")
                except Exception as e:
                    logger.warning(f"Не удалось удалить watch_later: {e}")

            # Добавляем отсутствующие колонки
            column_definitions = {
                "watched": "ALTER TABLE movies ADD COLUMN watched INTEGER DEFAULT 0",
                "watched_at": "ALTER TABLE movies ADD COLUMN watched_at TEXT",
                "added_at": "ALTER TABLE movies ADD COLUMN added_at TEXT DEFAULT (datetime('now'))"
            }

            for col_name, sql in column_definitions.items():
                if col_name not in columns:
                    await db.execute(sql)
                    logger.info(f"Добавлена колонка: {col_name}")

            # Проверяем индексы
            async with db.execute("PRAGMA index_list(movies)") as cursor:
                index_names = {row[1] for row in await cursor.fetchall()}

            required_indexes = {
                "idx_user_watched": "CREATE INDEX idx_user_watched ON movies(user_id, watched)",
                "idx_user_genre": "CREATE INDEX idx_user_genre ON movies(user_id, genre)",
                "idx_user_title_lower": "CREATE INDEX idx_user_title_lower ON movies(user_id, LOWER(title))"
            }

            for idx_name, sql in required_indexes.items():
                if idx_name not in index_names:
                    await db.execute(sql)
                    logger.info(f"Создан индекс: {idx_name}")

            # Фиксируем все изменения
            await db.commit()
            logger.info("✅ База данных инициализирована, обновлена и проиндексирована")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise