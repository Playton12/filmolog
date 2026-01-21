"""
Сервис для управления фильмами.
Изолирует бизнес-логику от обработчиков.
"""

from typing import List, Optional, Dict
import aiosqlite

from movie_bot.database.queries import (
    get_all_movies,
    get_movie_by_id,
    add_movie,
    mark_movie_watched,
    delete_movie,
    is_movie_exists,
    update_movie,
    get_movies_by_genre,
)
from movie_bot.utils.helpers import get_similar_movies as fuzzy_match


class MovieService:
    """
    Бизнес-логика управления фильмами.
    Все методы — асинхронные, изолированы от обработчиков.
    """

    @staticmethod
    async def get_all(user_id: int, watched: Optional[bool] = None) -> List[aiosqlite.Row]:
        """
        Получить все фильмы пользователя.
        """
        return await get_all_movies(user_id=user_id, watched=watched)

    @staticmethod
    async def get_by_id(user_id: int, movie_id: int) -> Optional[Dict]:
        """
        Получить фильм по ID.
        """
        return await get_movie_by_id(user_id, movie_id)

    @staticmethod
    async def create(
        user_id: int,
        title: str,
        genre: str,
        description: Optional[str] = None,
        poster_id: Optional[str] = None
    ) -> None:
        """
        Добавить новый фильм.
        """
        await add_movie(
            user_id=user_id,
            title=title,
            genre=genre,
            description=description,
            poster_id=poster_id
        )

    @staticmethod
    async def mark_watched(movie_id: int, user_id: int, watched: bool) -> None:
        """
        Пометить как просмотренный/непросмотренный.
        """
        await mark_movie_watched(movie_id, user_id, watched)

    @staticmethod
    async def remove(movie_id: int, user_id: int) -> Optional[str]:
        """
        Удалить фильм. Возвращает название или None.
        """
        return await delete_movie(movie_id, user_id)

    @staticmethod
    async def exists(user_id: int, title: str) -> bool:
        """
        Проверить, есть ли фильм с таким названием у пользователя.
        """
        return await is_movie_exists(user_id, title)

    @staticmethod
    async def update(user_id: int, movie_id: int, **fields) -> None:
        """
        Обновить поля фильма.
        """
        await update_movie(user_id, movie_id, **fields)

    @staticmethod
    async def get_recommendations(user_id: int, genre: str) -> List[aiosqlite.Row]:
        """
        Получить непросмотренные фильмы заданного жанра для пользователя.
        Используется в рекомендациях.
        """
        return await get_movies_by_genre(genre=genre, user_id=user_id)

    @staticmethod
    async def find_similar(user_id: int, title: str, threshold: int = 75) -> List[str]:
        """
        Найти похожие по названию (по fuzzy-сравнению).
        Возвращает список похожих названий.
        """
        movies = await get_all_movies(user_id=user_id, watched=None)
        # Приводим к списку словарей или Row — get_similar_movies поддерживает
        return fuzzy_match(movies, title, threshold)