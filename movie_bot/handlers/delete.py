"""
Обработчики удаления фильмов.

Функции:
- delete_movie_start — показывает список для удаления
- delete_movie_handler — удаляет выбранный фильм
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from movie_bot.database.queries import delete_movie
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.database.queries import get_all_movies
from movie_bot.keyboards.utils import get_movies_keyboard

router = Router()

@router.callback_query(F.data == "delete_menu")
async def delete_movie_start(callback: CallbackQuery):
    """
    Начинает процесс удаления: показывает список фильмов.

    :param callback: Callback от кнопки "Удалить фильм"
    """
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id)
    if not movies:
        await clear_and_send(callback.message, "📭 Нет фильмов для удаления.", await get_main_menu_with_stats(user_id))
        await callback.answer()
        return

    await clear_and_send(callback.message, "Выберите фильм для удаления:", get_movies_keyboard(movies, "delete"))
    await callback.answer()

@router.callback_query(F.data.startswith("delete:"))
async def delete_movie_handler(callback: CallbackQuery):
    """
    Удаляет выбранный фильм из базы.

    :param callback: Callback с ID фильма
    """
    try:
        movie_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка ID")
        return

    user_id = callback.from_user.id
    title = await delete_movie(movie_id, user_id)

    text = f"🗑 Фильм *{title}*" if title else "❌ Фильм не найден"
    text += " удалён." if title else " уже удалён."

    await clear_and_send(callback.message, text, await get_main_menu_with_stats(user_id), parse_mode="Markdown")
    await callback.answer()