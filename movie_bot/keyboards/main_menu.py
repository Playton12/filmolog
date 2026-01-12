"""
Генерация главного меню с динамической статистикой.

Функции:
- get_main_menu_with_stats — главное меню с количеством просмотренных фильмов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from movie_bot.database.queries import get_all_movies

async def get_main_menu_with_stats(user_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует главное меню с отображением количества просмотренных фильмов.

    :param user_id: ID пользователя
    :return: Inline-клавиатура с кнопками
    """
    movies = await get_all_movies(user_id=user_id, watched=True)
    count = len(movies)
    watched_text = f"✅ Просмотрено ({count})" if count > 0 else "✅ Просмотрено"

    buttons = [
        [InlineKeyboardButton(text="🎬 Получить рекомендацию", callback_data="recommend")],
        [InlineKeyboardButton(text="➕ Добавить фильм", callback_data="add")],
        [InlineKeyboardButton(text="📂 Мои фильмы", callback_data="my_movies")],
        [InlineKeyboardButton(text=watched_text, callback_data="watched_list")],
        [InlineKeyboardButton(text="🗑 Удалить фильм", callback_data="delete_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)