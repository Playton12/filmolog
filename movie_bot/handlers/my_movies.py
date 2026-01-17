"""
Обработчики для просмотра своих фильмов с поиском.
Теперь с поддержкой контекста: возврат в правильный список.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from movie_bot.fsm.states import MyMovies
from movie_bot.database.queries import get_all_movies, get_movie_by_id, mark_movie_watched
from movie_bot.keyboards.utils import get_cancel_button
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send

# Импорт пагинации
from movie_bot.utils.pagination import send_movie_page, send_search_page

router = Router()

ITEMS_PER_PAGE = 5  # Можно менять


@router.callback_query(F.data == "my_movies")
async def my_movies_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    all_movies = await get_all_movies(user_id=user_id, watched=None)
    total = len(all_movies)
    watched_count = len([m for m in all_movies if m["watched"]])
    unwatched_count = total - watched_count

    if total == 0:
        await clear_and_send(
            callback.message,
            "📭 У вас пока нет добавленных фильмов.\n\n"
            "Добавьте первый фильм — нажмите «➕ Добавить фильм»",
            await get_main_menu_with_stats(user_id)
        )
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Все ({total})", callback_data="my_movies_all")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="my_movies_search")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

    await clear_and_send(
        callback.message,
        f"📂 У вас {total} фильм{'ов' if total % 10 not in [2,3,4] or total // 10 == 1 else 'а'}.\n"
        "Выберите действие:",
        keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "my_movies_all")
async def my_movies_all_submenu(callback: CallbackQuery):
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=None)
    total = len(movies)
    watched_count = len([m for m in movies if m["watched"]])
    unwatched_count = len([m for m in movies if not m["watched"]])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Просмотренные ({watched_count})", callback_data="my_movies_watched")],
        [InlineKeyboardButton(text=f"⭕ Непросмотренные ({unwatched_count})", callback_data="my_movies_unwatched")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_movies")]
    ])

    await clear_and_send(
        callback.message,
        f"🎬 У вас {total} фильмов.\n\n"
        "Выберите категорию:",
        keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "my_movies_watched")
async def show_watched_movies(callback: CallbackQuery):
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=True)

    if not movies:
        await clear_and_send(
            callback.message,
            "⭕ У вас пока нет просмотренных фильмов.",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Другая категория", callback_data="my_movies_all")],
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_movies")]
            ])
        )
        await callback.answer()
        return

    await send_movie_page(callback, movies, 0, "watched", ITEMS_PER_PAGE)


@router.callback_query(F.data == "my_movies_unwatched")
async def show_unwatched_movies(callback: CallbackQuery):
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=False)

    if not movies:
        await clear_and_send(
            callback.message,
            "📭 У вас нет непросмотренных фильмов.",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Другая категория", callback_data="my_movies_all")],
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_movies")]
            ])
        )
        await callback.answer()
        return

    await send_movie_page(callback, movies, 0, "unwatched", ITEMS_PER_PAGE)


@router.callback_query(F.data.startswith("prev:"))
@router.callback_query(F.data.startswith("next:"))
async def navigate_page(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        direction = "prev" if callback.data.startswith("prev") else "next"
        view = parts[1]
        current_page = int(parts[2])
        page = current_page - 1 if direction == "prev" else current_page + 1

        user_id = callback.from_user.id
        watched = True if view == "watched" else False if view == "unwatched" else None
        movies = await get_all_movies(user_id=user_id, watched=watched)

        if not movies:
            await callback.answer("❌ Список пуст", show_alert=True)
            return

        await send_movie_page(callback, movies, page, view, ITEMS_PER_PAGE)
    except Exception as e:
        await callback.answer("❌ Ошибка при переключении страницы")
        print(f"[pagination] Ошибка: {e}")


@router.callback_query(F.data == "my_movies_search")
async def start_search_movies(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MyMovies.search)
    await clear_and_send(
        callback.message,
        "🔍 Введите название или жанр для поиска:",
        get_cancel_button()
    )
    await callback.answer()


@router.message(MyMovies.search)
async def search_movies(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("❌ Введите текст для поиска.", reply_markup=get_cancel_button())
        return

    query = message.text.strip().lower()
    user_id = message.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=None)

    results = [
        movie for movie in movies
        if query in movie["title"].lower() or query in movie["genre"].lower()
    ]

    if not results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="my_movies_search")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="my_movies")]
        ])
        await message.answer(
            f"❌ Ничего не найдено по запросу *{query}*.\n\n"
            "Попробуйте другое слово.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    await state.update_data(search_results=results, search_query=query)
    await send_search_page(message, results, 0, state, ITEMS_PER_PAGE)


@router.callback_query(F.data.startswith("prev_search:"))
@router.callback_query(F.data.startswith("next_search:"))
async def navigate_search_page(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        direction = "prev" if callback.data.startswith("prev") else "next"
        current_page = int(parts[1])
        page = current_page - 1 if direction == "prev" else current_page + 1

        data = await callback.bot.get_fsm_context(callback.bot.session, callback.from_user.id, callback.from_user.id).get_data()
        results = data.get("search_results", [])
        if not results:
            await callback.answer("❌ Результаты поиска утеряны", show_alert=True)
            return

        await send_search_page(callback.message, results, page, callback.bot.get_fsm_context(callback.bot.session, callback.from_user.id, callback.from_user.id), ITEMS_PER_PAGE)
    except Exception as e:
        await callback.answer("❌ Ошибка")
        print(f"[search pagination] {e}")


@router.callback_query(F.data.startswith("movie_info:"))
async def show_movie_info(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        movie_id = int(parts[1])
        source = parts[2] if len(parts) > 2 else "my_movies"
        await send_movie_card(callback, movie_id, source)
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
        await callback.answer()


async def send_movie_card(callback_or_message, movie_id: int, source: str = "my_movies"):
    user_id = None
    if isinstance(callback_or_message, CallbackQuery):
        user_id = callback_or_message.from_user.id
        message = callback_or_message.message
        bot = callback_or_message.bot
    elif isinstance(callback_or_message, Message):
        user_id = callback_or_message.from_user.id
        message = callback_or_message
        bot = callback_or_message.bot
    else:
        return

    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.answer("❌ Фильм не найден.")
            await callback_or_message.answer()
        else:
            await callback_or_message.answer("❌ Фильм не найден.")
        return

    from movie_bot.utils.helpers import get_movie_card_text
    text = get_movie_card_text(movie)

    back_callback = {
        "watched": "my_movies_watched",
        "unwatched": "my_movies_unwatched",
        "all": "my_movies_all",
        "search": "my_movies_search"
    }.get(source, "my_movies")

    watched_status = "✅ Пометить как непросмотренный" if movie["watched"] else "⭕ Пометить как просмотренный"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=watched_status, callback_data=f"toggle_watched:{movie_id}:{source}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_select:{movie_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{movie_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data=back_callback)]
    ])

    try:
        if movie.get("poster_id"):
            await clear_and_send(message, "Загрузка...", None)
            await message.answer_photo(
                photo=movie["poster_id"],
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await clear_and_send(
                message,
                text,
                keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке карточки: {e}")


@router.callback_query(F.data.startswith("toggle_watched:"))
async def toggle_watched_status(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        movie_id = int(parts[1])
        source = parts[2] if len(parts) > 2 else "my_movies"
        user_id = callback.from_user.id

        movie = await get_movie_by_id(user_id, movie_id)
        if not movie:
            await callback.message.answer("❌ Фильм не найден.")
            await callback.answer()
            return

        new_watched = not movie["watched"]
        await mark_movie_watched(movie_id, user_id, new_watched)

        updated_movie = await get_movie_by_id(user_id, movie_id)
        if not updated_movie:
            await callback.message.answer("❌ Ошибка: фильм исчез.")
            await callback.answer()
            return

        from movie_bot.utils.helpers import get_movie_card_text
        text = get_movie_card_text(updated_movie)

        back_callback = {
            "watched": "my_movies_watched",
            "unwatched": "my_movies_unwatched",
            "all": "my_movies_all",
            "search": "my_movies_search"
        }.get(source, "my_movies")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Пометить как непросмотренный" if new_watched else "⭕ Пометить как просмотренный",
                callback_data=f"toggle_watched:{movie_id}:{source}"
            )],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_select:{movie_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{movie_id}")],
            [InlineKeyboardButton(text="🔙 Назад к списку", callback_data=back_callback)]
        ])

        if movie.get("poster_id"):
            await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        await callback.answer("🟢 Обновлено!", show_alert=False, cache_time=1)

    except Exception as e:
        await callback.answer("❌ Ошибка при обновлении.")
        print(f"[toggle_watched] Ошибка: {e}")