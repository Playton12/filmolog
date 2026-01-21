"""
Клавиатура главного меню с красивой статистикой.
"""

from aiogram.types import InlineKeyboardMarkup
from movie_bot.database import get_all_movies
from movie_bot.keyboards.factory import KeyboardFactory
from movie_bot.utils.text_builder import TextBuilder
from movie_bot.services.user_service import UserService


async def get_main_menu_with_stats(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    try:
        stats = await UserService.get_stats(user_id)
        stats_text = TextBuilder.main_menu_stats(**stats)
        keyboard = KeyboardFactory.main_menu()
        return stats_text, keyboard
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.error(f"[main_menu] Ошибка при получении статистики: {e}")
        return "📊 Статистика недоступна", KeyboardFactory.main_menu()