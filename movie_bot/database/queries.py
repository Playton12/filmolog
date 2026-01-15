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
from movie_bot.database.db import get_db

logger = logging.getLogger(__name__)

async def get_all_movies(user_id: int, watched: bool = None, order: str = "id"):
    """
    Возвращает все фильмы пользователя с возможной фильтрацией по статусу "просмотрен".

    :param user_id: ID пользователя в Telegram
    :param watched: Фильтр по статусу просмотра (True — просмотренные, False — непросмотренные, None — всё)
    :param order: Поле для сортировки (например, 'id', 'added_at DESC')
    :return: Список строк (aiosqlite.Row) с данными фильмов
    """
    async with get_db() as db:
        query = "SELECT id, title, genre, description, poster_id, added_at, watched FROM movies WHERE user_id = ?"
        params = [user_id]
        if watched is not None:
            query += " AND watched = ?"
            params.append(1 if watched else 0)
        query += f" ORDER BY {order}"
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            logger.debug(f"Получено {len(rows)} фильмов: user_id={user_id}, watched={watched}")
            return rows

async def get_movies_by_genre(genre: str):
    """
    Возвращает непросмотренные фильмы заданного жанра.

    Используется для рекомендаций.

    :param genre: Название жанра (должно совпадать с GENRES)
    :return: Список фильмов без постера
    """
    async with get_db() as db:
        async with db.execute(
            "SELECT title, description, poster_id FROM movies WHERE genre = ? AND watched = 0",
            (genre,)
        ) as cursor:
            return await cursor.fetchall()
        
async def get_movie_by_id(user_id: int, movie_id: int):
    """
    Возвращает данные одного фильма по ID и пользователю.

    :param user_id: ID пользователя
    :param movie_id: ID фильма
    :return: Row с данными фильма или None
    """
    async with get_db() as db:
        async with db.execute(
            "SELECT id, title, genre, description, poster_id, watched FROM movies WHERE id = ? AND user_id = ?",
            (movie_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def add_movie(user_id: int, title: str, genre: str, description: str, poster_id: str = None):
    """
    Добавляет новый фильм в базу данных.

    :param user_id: ID пользователя
    :param title: Название фильма
    :param genre: Жанр
    :param description: Описание
    :param poster_id: ID фото в Telegram (опционально)
    """
    async with get_db() as db:
        await db.execute(
            "INSERT INTO movies (user_id, title, genre, description, poster_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, genre, description, poster_id)
        )
        await db.commit()
        logger.info(f"Фильм добавлен: {title} | user_id={user_id}")

async def delete_movie(movie_id: int, user_id: int) -> str:
    """
    Удаляет фильм из коллекции, если он принадлежит пользователю.

    :param movie_id: ID фильма
    :param user_id: ID владельца
    :return: Название фильма, если удалён, иначе None
    """
    async with get_db() as db:
        async with db.execute("SELECT title FROM movies WHERE id = ? AND user_id = ?", (movie_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            await db.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            await db.commit()
            return row["title"]

async def is_movie_exists(user_id: int, title: str) -> bool:
    """
    Проверяет, есть ли фильм с таким названием у пользователя.

    :param user_id: ID пользователя
    :param title: Название фильма
    :return: True, если существует
    """
    async with get_db() as db:
        async with db.execute(
            "SELECT 1 FROM movies WHERE user_id = ? AND LOWER(title) = LOWER(?)",
            (user_id, title)
        ) as cursor:
            return bool(await cursor.fetchone())

async def mark_movie_watched(movie_id: int, user_id: int, watched: bool):
    """
    Отмечает фильм как просмотренный или непросмотренный.

    :param movie_id: ID фильма
    :param user_id: ID пользователя
    :param watched: True — просмотрен, False — нет
    """
    async with get_db() as db:
        await db.execute(
            "UPDATE movies SET watched = ? WHERE id = ? AND user_id = ?",
            (1 if watched else 0, movie_id, user_id)
        )
        await db.commit()

async def update_movie(user_id: int, movie_id: int, **kwargs):
    """
    Обновляет поля фильма.

    :param user_id: ID владельца фильма
    :param movie_id: ID фильма
    :param kwargs: Поля для обновления (например, title='Новое название')
    """
    if not kwargs:
        return

    async with get_db() as db:
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE movies SET {set_clause} WHERE id = ? AND user_id = ?"
        params = list(kwargs.values()) + [movie_id, user_id]
        await db.execute(query, params)
        await db.commit()
        logger.info(f"Фильм обновлён: {movie_id} | user_id={user_id} | Изменено: {list(kwargs.keys())}")