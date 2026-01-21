"""
Модуль с SQL-запросами к базе данных.

Содержит асинхронные функции для:
- Получения фильмов
- Добавления
- Удаления
- Проверки дубликатов
- Отметки как просмотренных
"""

import logging
from typing import List, Optional, Dict
import aiosqlite

from movie_bot.database.db import get_db, ALLOWED_ORDER_FIELDS

logger = logging.getLogger(__name__)

async def get_all_movies(
    user_id: int,
    watched: Optional[bool] = None,
    order: str = "added_at DESC"
) -> List[aiosqlite.Row]:
    """
    Возвращает все фильмы пользователя с фильтрацией и сортировкой.
    """
    # Защита от SQL-инъекции
    order_field = order.strip()
    if " " in order_field:
        field, direction = order_field.rsplit(" ", 1)
        if field not in ALLOWED_ORDER_FIELDS or direction.upper() not in {"ASC", "DESC"}:
            order_field = "added_at DESC"
    elif order_field not in ALLOWED_ORDER_FIELDS:
        order_field = "added_at DESC"

    query = f"""
        SELECT id, title, genre, description, poster_id, watched, added_at, watched_at
        FROM movies
        WHERE user_id = ?
    """
    params = [user_id]

    if watched is not None:
        query += " AND watched = ?"
        params.append(1 if watched else 0)

    query += f" ORDER BY {order_field}"

    async with get_db() as db:
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            logger.debug(f"Получено {len(rows)} фильмов: user_id={user_id}, watched={watched}")
            return rows


async def get_movies_by_genre(
    genre: str,
    user_id: int
) -> List[aiosqlite.Row]:
    """
    Возвращает непросмотренные фильмы заданного жанра для указанного пользователя.

    Используется для рекомендаций.
    Включает: id, title, genre, description, poster_id.

    :param genre: Точный жанр (должен совпадать с базой)
    :param user_id: Telegram ID пользователя
    :return: Список строк (aiosqlite.Row) с фильмами
    """
    async with get_db() as db:
        async with db.execute(
            """
            SELECT id, title, genre, description, poster_id
            FROM movies
            WHERE genre = ? AND watched = 0 AND user_id = ?
            """,
            (genre, user_id)
        ) as cursor:
            return await cursor.fetchall()


async def get_movie_by_id(user_id: int, movie_id: int) -> Optional[Dict]:
    """
    Возвращает данные фильма по ID и пользователю.
    """
    async with get_db() as db:
        async with db.execute(
            """
            SELECT id, title, genre, description, poster_id, watched, added_at, watched_at
            FROM movies
            WHERE id = ? AND user_id = ?
            """,
            (movie_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_movie(
    user_id: int,
    title: str,
    genre: str,
    description: str,
    poster_id: Optional[str] = None
):
    """
    Добавляет фильм. Использует CURRENT_TIMESTAMP.
    """
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO movies (user_id, title, genre, description, poster_id, added_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, title, genre, description, poster_id)
        )
        await db.commit()
        logger.info(f"Фильм добавлен: {title} | user_id={user_id}")


async def delete_movie(movie_id: int, user_id: int) -> Optional[str]:
    """
    Удаляет фильм. Возвращает название или None.
    """
    async with get_db() as db:
        async with db.execute(
            "SELECT title FROM movies WHERE id = ? AND user_id = ?",
            (movie_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            await db.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            await db.commit()
            return row["title"]


async def is_movie_exists(user_id: int, title: str) -> bool:
    """
    Проверяет, есть ли фильм с таким названием у пользователя.
    """
    async with get_db() as db:
        async with db.execute(
            "SELECT 1 FROM movies WHERE user_id = ? AND LOWER(title) = LOWER(?)",
            (user_id, title)
        ) as cursor:
            return bool(await cursor.fetchone())


async def mark_movie_watched(movie_id: int, user_id: int, watched: bool):
    """
    Отмечает фильм как просмотренный/непросмотренный.
    """
    async with get_db() as db:
        if watched:
            await db.execute(
                "UPDATE movies SET watched = 1, watched_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (movie_id, user_id)
            )
        else:
            await db.execute(
                "UPDATE movies SET watched = 0, watched_at = NULL WHERE id = ? AND user_id = ?",
                (movie_id, user_id)
            )
        await db.commit()


async def update_movie(user_id: int, movie_id: int, **kwargs):
    """
    Обновляет поля фильма. Защита от SQL-инъекций.
    """
    if not kwargs:
        return

    # Только разрешённые поля
    allowed_fields = {"title", "genre", "description", "poster_id", "watched", "watched_at"}
    valid_keys = [k for k in kwargs if k in allowed_fields]
    if not valid_keys:
        logger.warning(f"Попытка обновить недопустимые поля: {set(kwargs.keys()) - allowed_fields}")
        return

    set_clause = ", ".join([f"{key} = ?" for key in valid_keys])
    query = f"UPDATE movies SET {set_clause} WHERE id = ? AND user_id = ?"
    params = [kwargs[key] for key in valid_keys] + [movie_id, user_id]

    async with get_db() as db:
        await db.execute(query, params)
        await db.commit()
        logger.info(f"Фильм обновлён: {movie_id} | user_id={user_id} | Поля: {valid_keys}")

__all__ = [
    "get_all_movies",
    "get_movies_by_genre",
    "get_movie_by_id",
    "add_movie",
    "delete_movie",
    "is_movie_exists",
    "mark_movie_watched",
    "update_movie",
]