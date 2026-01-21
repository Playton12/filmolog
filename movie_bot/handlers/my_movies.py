"""
Обработчики для просмотра своих фильмов с поиском.
Теперь с поддержкой контекста, KeyboardFactory и безопасной отправкой.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from movie_bot.fsm import MyMovies
from movie_bot.database import get_all_movies, get_movie_by_id, mark_movie_watched
from movie_bot.keyboards.factory import KeyboardFactory
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.utils.pagination import send_movie_page, send_search_page
from movie_bot.utils.text_builder import TextBuilder
from movie_bot.config import ITEMS_PER_PAGE

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("my_movies"))
@router.callback_query(F.data == "my_movies")
async def my_movies_menu(event, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=None)
    total = len(movies)

    if total == 0:
        stats_text, keyboard = await get_main_menu_with_stats(user_id)
        await clear_and_send(event, TextBuilder.no_movies_yet(), keyboard)
        return

    watched_count = sum(1 for m in movies if m["watched"])
    await clear_and_send(
        event,
        TextBuilder.my_movies_intro(total=total, watched=watched_count),
        KeyboardFactory.my_movies_menu(total=total)
    )

@router.callback_query(F.data == "my_movies_all")
async def my_movies_all_submenu(callback: CallbackQuery):
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=None)
    watched_count = sum(1 for m in movies if m["watched"])
    unwatched_count = len(movies) - watched_count

    await clear_and_send(
        callback.message,
        f"🎬 У вас {len(movies)} контента.\n\nВыберите категорию:",
        KeyboardFactory.movies_filter(watched_count, unwatched_count)
    )
    await callback.answer()

@router.callback_query(F.data == "my_movies_watched")
async def show_watched_movies(callback: CallbackQuery):
    movies = await get_all_movies(user_id=callback.from_user.id, watched=True)
    if not movies:
        await clear_and_send(
            callback.message,
            TextBuilder.no_watched_movies(),
            KeyboardFactory.after_empty("watched")
        )
        await callback.answer()
        return
    await send_movie_page(callback, movies, 0, "watched", ITEMS_PER_PAGE)


@router.callback_query(F.data == "my_movies_unwatched")
async def show_unwatched_movies(callback: CallbackQuery):
    movies = await get_all_movies(user_id=callback.from_user.id, watched=False)
    if not movies:
        await clear_and_send(
            callback.message,
            TextBuilder.no_unwatched_movies(),
            KeyboardFactory.after_empty("unwatched")
        )
        await callback.answer()
        return
    await send_movie_page(callback, movies, 0, "unwatched", ITEMS_PER_PAGE)

@router.callback_query(F.data.startswith("prev:") | F.data.startswith("next:"))
async def navigate_page(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        direction = "prev" if callback.data.startswith("prev") else "next"
        view = parts[1]
        page = int(parts[2]) + (1 if direction == "next" else -1)

        watched = {"watched": True, "unwatched": False}.get(view)
        movies = await get_all_movies(user_id=callback.from_user.id, watched=watched)

        if not movies:
            await callback.answer("❌ Список пуст", show_alert=True)
            return

        await send_movie_page(callback, movies, page, view, ITEMS_PER_PAGE)
    except Exception as e:
        logger.error(f"[pagination] Ошибка при переключении: {e}")
        await callback.answer("❌ Ошибка при переключении страницы")

@router.callback_query(F.data == "my_movies_search")
async def start_search_movies(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MyMovies.search_query)
    await clear_and_send(
        callback.message,
        TextBuilder.prompt_search(),
        KeyboardFactory.cancel(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(MyMovies.search_query)
async def search_movies(message: Message, state: FSMContext):
    query = message.text.strip().lower() if message.text else ""
    if not query:
        await message.answer(TextBuilder.err_search_empty(), reply_markup=KeyboardFactory.cancel())
        return

    user_id = message.from_user.id
    all_movies = await get_all_movies(user_id=user_id, watched=None)
    results = [
        movie for movie in all_movies
        if query in movie["title"].lower() or query in movie["genre"].lower()
    ]

    if not results:
        await clear_and_send(
            message,
            TextBuilder.search_no_results(query),
            KeyboardFactory.retry_search()
        )
        return

    await state.update_data(search_results=results, search_query=query)
    await send_search_page(message, results, 0, state, ITEMS_PER_PAGE)

@router.callback_query(F.data.startswith("prev_search:") | F.data.startswith("next_search:"))
async def navigate_search_page(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split(":")
        direction = "prev" if callback.data.startswith("prev") else "next"
        page = int(parts[1]) + (1 if direction == "next" else -1)

        data = await state.get_data()
        results = data.get("search_results", [])

        if not results:
            await callback.answer("❌ Результаты утеряны", show_alert=True)
            return

        await send_search_page(callback.message, results, page, state, ITEMS_PER_PAGE)
    except Exception as e:
        logger.error(f"[search pagination] Ошибка: {e}")
        await callback.answer("❌ Ошибка при навигации")

@router.callback_query(F.data.startswith("movie_info:"))
async def show_movie_info(callback: CallbackQuery):
    try:
        parts = callback.data.split(":", 2)
        movie_id = int(parts[1])
        source = parts[2] if len(parts) > 2 else "my_movies"
        await send_movie_card(callback, movie_id, source)
        await callback.answer()
    except Exception as e:
        logger.error(f"[movie_info] Ошибка: {e}")
        await callback.message.answer("❌ Ошибка при открытии фильма.")


async def send_movie_card(event, movie_id: int, source: str = "my_movies"):
    user_id = event.from_user.id
    message = event.message if isinstance(event, CallbackQuery) else event

    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await message.answer("❌ Контент не найден.")
        return

    text = TextBuilder.movie_card(movie)
    keyboard = KeyboardFactory.movie_actions(source=source, watched=movie["watched"], movie_id=movie["id"])

    toggle_text = TextBuilder.btn_toggle_watched(not movie["watched"])
    toggle_callback = f"toggle_watched:{movie_id}:{source}"

    # Обновляем текст и callback кнопки
    for row in keyboard.inline_keyboard:
        for btn in row:
            if "Пометить" in btn.text or "Смотреть" in btn.text:
                btn.text = toggle_text
                btn.callback_data = toggle_callback

    try:
        if movie.get("poster_id"):
            await clear_and_send(message, TextBuilder.loading(), None)
            await message.answer_photo(
                photo=movie["poster_id"],
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await clear_and_send(message, text, keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"[send_movie_card] Ошибка при отправке: {e}")
        await message.answer("❌ Не удалось отправить карточку.")

@router.callback_query(F.data.startswith("toggle_watched:"))
async def toggle_watched_status(callback: CallbackQuery):
    try:
        parts = callback.data.split(":", 3)
        movie_id = int(parts[1])
        source = parts[2] if len(parts) > 2 else "my_movies"
        user_id = callback.from_user.id

        movie = await get_movie_by_id(user_id, movie_id)
        if not movie:
            await callback.message.answer("❌ Контент не найден.")
            await callback.answer()
            return

        new_watched = not movie["watched"]
        await mark_movie_watched(movie_id, user_id, new_watched)

        updated = await get_movie_by_id(user_id, movie_id)
        if not updated:
            await callback.message.answer("❌ Ошибка загрузки фильма.")
            await callback.answer()
            return

        text = TextBuilder.movie_card(updated)
        keyboard = KeyboardFactory.movie_actions(source=source, watched=new_watched, movie_id=movie["id"])

        toggle_text = TextBuilder.btn_toggle_watched(not new_watched)
        toggle_callback = f"toggle_watched:{movie_id}:{source}"

        for row in keyboard.inline_keyboard:
            for btn in row:
                if "Пометить" in btn.text or "Смотреть" in btn.text:
                    btn.text = toggle_text
                    btn.callback_data = toggle_callback

        if movie.get("poster_id"):
            await callback.message.edit_caption(
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        await callback.answer("🟢 Обновлено!", cache_time=1)
    except Exception as e:
        logger.error(f"[toggle_watched] Ошибка: {e}")
        await callback.answer("❌ Ошибка при обновлении.", cache_time=3)