"""
Утилита для пагинации списков фильмов.
Теперь с поддержкой конфигурации и единым стилем.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from movie_bot.utils.helpers import clear_and_send
from movie_bot.config import ITEMS_PER_PAGE
from movie_bot.utils.text_builder import TextBuilder


async def send_movie_page(
    callback,
    movies: list,
    page: int,
    view: str,
    items_per_page: int = None
):
    """
    Показывает страницу фильмов с пагинацией.

    :param callback: CallbackQuery
    :param movies: Список фильмов
    :param page: Номер страницы (0..N)
    :param view: 'watched', 'unwatched'
    :param items_per_page: Количество элементов на странице (по умолчанию из config)
    """
    if items_per_page is None:
        items_per_page = ITEMS_PER_PAGE

    total = len(movies)
    total_pages = (total + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    page_items = movies[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Список фильмов
    for movie in page_items:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {movie['title']}",
                callback_data=f"movie_info:{movie['id']}:{view}"
            )
        ])

    # Навигация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"prev:{view}:{page}"
        ))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Вперёд ▶️",
            callback_data=f"next:{view}:{page}"
        ))
    if nav_row:
        keyboard.inline_keyboard.append(nav_row)

    # Управление
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔄 Другая категория", callback_data="my_movies_all")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_movies")
    ])

    # Заголовок
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
    items_per_page: int = None
):
    """
    Показывает страницу результатов поиска с пагинацией.

    :param message: Message (для ответа)
    :param results: Список найденных фильмов
    :param page: Номер страницы
    :param state: FSMContext (для получения запроса)
    :param items_per_page: Элементов на странице
    """
    if items_per_page is None:
        items_per_page = ITEMS_PER_PAGE

    total = len(results)
    total_pages = (total + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    page_items = results[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Фильмы
    for movie in page_items:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {movie['title']}",
                callback_data=f"movie_info:{movie['id']}:search"
            )
        ])

    # Навигация
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"prev_search:{page}"
        ))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Вперёд ▶️",
            callback_data=f"next_search:{page}"
        ))
    if nav_row:
        keyboard.inline_keyboard.append(nav_row)

    # Кнопки
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔄 Другой запрос", callback_data="my_movies_search")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="my_movies")
    ])

    # Получаем запрос из состояния
    data = await state.get_data()
    query = data.get("search_query", "неизвестный запрос")

    page_info = f" | Страница {page + 1}/{total_pages}" if total_pages > 1 else ""

    await message.answer(
    TextBuilder.search_results_text(total, query, page, total_pages),
    reply_markup=keyboard,
    parse_mode="HTML"
)