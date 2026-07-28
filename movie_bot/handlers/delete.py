"""
Обработчики удаления фильмов.

Теперь с подтверждением, безопасным удалением и фабрикой клавиатур.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramForbiddenError

from movie_bot.database import get_movie_by_id, delete_movie, get_all_movies
from movie_bot.utils.pagination import send_movie_page
from movie_bot.keyboards.factory import KeyboardFactory
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.utils.text_builder import TextBuilder
from movie_bot.config import ITEMS_PER_PAGE

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("delete:"))
async def delete_movie_confirm(callback: CallbackQuery):
    try:
        # Разбиваем: delete:123:my_movies_unwatched
        parts = callback.data.split(":", 2)
        movie_id = int(parts[1])
        source = parts[2] if len(parts) > 2 else "my_movies"
    except (ValueError, IndexError):
        await callback.answer("❌ Неверный ID фильма.", show_alert=True)
        return

    user_id = callback.from_user.id
    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await callback.answer("❌ Фильм не найден.", show_alert=True)
        return

    kb = KeyboardFactory.confirm_delete_for_movie(movie_id=movie_id, source=source)

    await clear_and_send(
        callback.message,
        TextBuilder.confirm_delete(movie['title']),
        kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete:"))
async def delete_movie_handler(callback: CallbackQuery):
    try:
        parts = callback.data.split(":", 2)
        movie_id = int(parts[1])
        source = parts[2] if len(parts) > 2 else "my_movies"
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка при парсинге ID.", show_alert=True)
        return

    user_id = callback.from_user.id
    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        return await _send_movie_not_found(callback)

    try:
        deleted_title = await delete_movie(movie_id, user_id)
        if not deleted_title:
            return await _send_movie_not_found(callback)
        logger.info(f"Пользователь {user_id} удалил: '{deleted_title}' (ID: {movie_id})")
    except Exception as e:
        logger.error(f"[delete] Ошибка при удалении фильма {movie_id}: {e}")
        await callback.message.answer("❌ Ошибка при удалении. Попробуйте позже.")
        await callback.answer()
        return

    await _send_deletion_success(callback, deleted_title, source)

async def _send_movie_not_found(callback: CallbackQuery):
    """Отправляет сообщение, если фильм уже удалён."""
    user_id = callback.from_user.id
    try:
        stats_text, keyboard = await get_main_menu_with_stats(user_id)
        await clear_and_send(callback.message, "🗑 Контент уже удалён или не существует.", keyboard)
    except TelegramForbiddenError:
        logger.warning(f"Бот не может писать пользователю {user_id}")
    await callback.answer()


async def _send_deletion_success(callback: CallbackQuery, title: str, source: str):
    user_id = callback.from_user.id
    try:
        view = "all"
        if "watched" in source:
            movies = await get_all_movies(user_id=user_id, watched=True)
            view = "watched"
        elif "unwatched" in source:
            movies = await get_all_movies(user_id=user_id, watched=False)
            view = "unwatched"
        else:
            movies = await get_all_movies(user_id=user_id, watched=None)

        if not movies:
            await clear_and_send(
                callback.message,
                TextBuilder.success_deleted(title),
                KeyboardFactory.after_empty(view),
                parse_mode="HTML"
            )
        else:
            await send_movie_page(callback, movies, 0, view, ITEMS_PER_PAGE)
    except Exception as e:
        logger.error(f"[delete] Ошибка при показе списка после удаления: {e}")
        stats_text, kb = await get_main_menu_with_stats(user_id)
        await clear_and_send(callback.message, TextBuilder.success_deleted(title), kb, parse_mode="HTML")
    await callback.answer()