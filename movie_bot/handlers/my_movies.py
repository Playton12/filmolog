"""
Обработчик команды "Мои фильмы".

Отображает все добавленные фильмы пользователя.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.text_decorations import markdown_decoration

from movie_bot.database.queries import get_all_movies
from movie_bot.keyboards.utils import get_movies_keyboard
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.handlers.watched import view_movie

router = Router()

@router.callback_query(F.data == "my_movies")
async def my_movies(callback: CallbackQuery):
    """
    Отображает список всех фильмов пользователя.

    :param callback: Callback от кнопки "Мои фильмы"
    """
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, order="added_at DESC")
    count = len(movies)

    if not movies:
        text = "📭 У вас пока нет фильмов."
        keyboard = await get_main_menu_with_stats(user_id)
    else:
        text = f"🎥 Ваши фильмы: *{count}* шт.\n\nВыберите для просмотра:"
        keyboard = get_movies_keyboard(movies, "view")

    await clear_and_send(callback.message, text, keyboard, parse_mode="Markdown")
    await callback.answer()