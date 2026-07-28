"""
Сервис для работы с пользователями.
Содержит бизнес-логику, связанную с профилем и статистикой.
"""

from typing import Dict
from movie_bot.database.queries import get_user_stats


class UserService:
    """
    Сервис управления пользователем: статистика, настройки, активность.
    """

    @staticmethod
    async def get_stats(user_id: int) -> Dict[str, int]:
        """
        Получить статистику пользователя через SQL COUNT.

        :param user_id: ID пользователя
        :return: Словарь с ключами: total, watched
        """
        return await get_user_stats(user_id)
