"""
Обработчики рекомендаций по жанрам.
Теперь с TextBuilder, KeyboardFactory и безопасной отправкой.
"""

import logging
import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from movie_bot.keyboards.genre import get_genre_keyboard, GENRES
from movie_bot.database import get_movies_by_genre
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.utils.text_builder import TextBuilder

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("recommend"))
@router.callback_query(F.data == "recommend")
async def recommend_menu(event):
    """
    Показывает меню выбора жанра для рекомендации.
    """
    await clear_and_send(
        event,
        TextBuilder.recommend_choose_genre(),
        get_genre_keyboard("rec"),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("rec_genre:"))
async def recommend_by_genre(callback: CallbackQuery):
    """
    Рекомендует случайный непросмотренный фильм из выбранного жанра.
    """
    await callback.answer()

    try:
        genre = callback.data.split(":", 1)[1]
    except IndexError:
        logger.warning(f"[recommend] Ошибка парсинга жанра у пользователя {callback.from_user.id}")
        await callback.message.answer("❌ Ошибка: не удалось определить жанр.")
        return

    # Проверка валидности жанра
    if genre not in GENRES:
        logger.warning(f"[recommend] Неверный жанр: {genre} от пользователя {callback.from_user.id}")
        await callback.message.answer("❌ Некорректный жанр.")
        return

    user_id = callback.from_user.id
    movies = await get_movies_by_genre(genre=genre, user_id=user_id)

    if not movies:
        return await _send_no_movies_in_genre(callback, genre, user_id)

    # Случайный фильм
    movie = random.choice(movies)
    caption = TextBuilder.recommend_movie_caption(movie)

    try:

        poster_id = movie["poster_id"] if movie["poster_id"] else None

        if poster_id:
            await clear_and_send(callback.message, TextBuilder.loading(), None)
            await callback.message.answer_photo(
                photo=movie["poster_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=(await get_main_menu_with_stats(user_id))[1]
            )
        else:
            await clear_and_send(
                callback.message,
                caption,
                (await get_main_menu_with_stats(user_id))[1],
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"[recommend] Ошибка отправки рекомендации: {e}")
        await callback.message.answer("❌ Не удалось показать рекомендацию.")

async def _send_no_movies_in_genre(callback: CallbackQuery, genre: str, user_id: int):
    """
    Отправляет сообщение, если в жанре нет фильмов.
    """
    try:
        text = TextBuilder.recommend_no_movies_in_genre(genre)
        _, keyboard = await get_main_menu_with_stats(user_id)
        await clear_and_send(callback.message, text, keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"[recommend] Ошибка при отправке 'нет фильмов': {e}")
        await callback.message.answer("❌ Ошибка загрузки меню.")