"""
Сервис для работы с пользователями.
Содержит бизнес-логику, связанную с профилем и статистикой.
"""

from typing import Dict, Optional
from movie_bot.services.movie_service import MovieService


class UserService:
    """
    Сервис управления пользователем: статистика, настройки, активность.
    """

    @staticmethod
    async def get_stats(user_id: int) -> Dict[str, int]:
        """
        Получить статистику пользователя: общее количество, просмотренные, непросмотренные.

        :param user_id: ID пользователя
        :return: Словарь с ключами: total, watched, unwatched
        """
        movies = await MovieService.get_all(user_id=user_id, watched=None)

        watched = 0
        for movie in movies:
            if movie["watched"]:
                watched += 1
        total = len(movies)

        return {
            "total": total,
            "watched": watched,
        }