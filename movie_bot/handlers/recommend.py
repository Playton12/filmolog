"""
Обработчики рекомендаций по жанрам.

Функции:
- recommend_menu — выбор жанра
- recommend_by_genre — показ фильма
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
import random

from movie_bot.keyboards.genre import get_genre_keyboard
from movie_bot.database.queries import get_movies_by_genre
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send


router = Router()

@router.callback_query(F.data == "recommend")
async def recommend_menu(callback: CallbackQuery):
    """
    Показывает меню выбора жанра для рекомендации.

    :param callback: Callback-запрос
    """
    await callback.answer()
    await clear_and_send(callback.message, "Выберите жанр:", get_genre_keyboard("rec"))

@router.callback_query(F.data.startswith("rec_genre:"))
async def recommend_by_genre(callback: CallbackQuery):
    """
    Рекомендует случайный непросмотренный фильм из выбранного жанра.

    :param callback: Callback-запрос с жанром
    """
    await callback.answer()
    try:
        genre = callback.data.split(":", 1)[1]
    except IndexError:
        return

    movies = await get_movies_by_genre(genre)
    if not movies:
        text = f"🤷‍♂️ В жанре *{genre}* пусто."
        keyboard = await get_main_menu_with_stats(callback.from_user.id)
        await clear_and_send(callback.message, text, keyboard, parse_mode="Markdown")
        return

    movie = random.choice(movies)
    caption = f"🎥 *{movie['title']}*\n\n📝 {movie['description']}"

    try:
        await callback.message.delete()
    except:
        pass

    if movie["poster_id"]:
        await callback.message.answer_photo(
            photo=movie["poster_id"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=await get_main_menu_with_stats(callback.from_user.id)
        )
    else:
        await callback.message.answer(caption, parse_mode="Markdown", reply_markup=await get_main_menu_with_stats(callback.from_user.id))