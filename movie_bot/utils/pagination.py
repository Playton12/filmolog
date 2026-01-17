"""
Утилита для пагинации списков фильмов.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from movie_bot.utils.helpers import clear_and_send


async def send_movie_page(
    callback,
    movies: list,
    page: int,
    view: str,
    items_per_page: int = 5
):
    """
    Показывает страницу фильмов с пагинацией.

    :param callback: CallbackQuery
    :param movies: Список всех фильмов
    :param page: Номер страницы (0..N)
    :param view: 'watched', 'unwatched'
    :param items_per_page: Элементов на странице
    """
    total = len(movies)
    total_pages = (total + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    page_items = movies[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for movie in page_items:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {movie['title']}",
                callback_data=f"movie_info:{movie['id']}:{view}"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"prev:{view}:{page}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"next:{view}:{page}"))
    if nav_row:
        keyboard.inline_keyboard.append(nav_row)

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔄 Другая категория", callback_data="my_movies_all")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_movies")
    ])

    titles = {
        "watched": "✅ Просмотренные",
        "unwatched": "⭕ Непросмотренные"
    }
    title = titles.get(view, "Фильмы")
    page_info = f" | Страница {page + 1}/{total_pages}" if total_pages > 1 else ""

    await clear_and_send(
        callback.message,
        f"{title} ({total}){page_info}:",
        keyboard
    )
    await callback.answer()


async def send_search_page(
    message,
    results: list,
    page: int,
    state: FSMContext,
    items_per_page: int = 5
):
    """
    Показывает страницу результатов поиска.
    """
    total = len(results)
    total_pages = (total + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    page_items = results[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for movie in page_items:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {movie['title']}",
                callback_data=f"movie_info:{movie['id']}:search"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"prev_search:{page}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"next_search:{page}"))
    if nav_row:
        keyboard.inline_keyboard.append(nav_row)

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔄 Другой запрос", callback_data="my_movies_search")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="my_movies")
    ])

    data = await state.get_data()
    query = data.get("search_query", "...")
    page_info = f" | Страница {page + 1}/{total_pages}" if total_pages > 1 else ""

    await message.answer(
        f"🔍 Найдено {total} по запросу\n"
        f"\"<i>{query}</i>\"{page_info}:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )