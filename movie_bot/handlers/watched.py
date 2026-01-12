"""
Обработчики для списка "Просмотрено" и просмотра карточки фильма.

Функции:
- watched_list — показывает просмотренные
- view_movie — отображает карточку фильма
- mark_as_watched / mark_as_unwatched — изменение статуса
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from movie_bot.database.queries import get_all_movies, mark_movie_watched
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send

router = Router()

# --- Список просмотренных ---
@router.callback_query(F.data == "watched_list")
async def watched_list(callback: CallbackQuery):
    """
    Отображает список просмотренных фильмов.

    :param callback: Callback от кнопки "Просмотрено"
    """
    await callback.answer()
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=True, order="added_at DESC")
    count = len(movies)

    if not movies:
        text = "📭 Вы пока ничего не посмотрели."
        keyboard = await get_main_menu_with_stats(user_id)
    else:
        text = f"✅ Вы посмотрели: *{count}* фильмов\n\nВыберите для просмотра:"
        buttons = [[InlineKeyboardButton(text=f"🎥 {m['title']}", callback_data=f"view:{m['id']}")] for m in movies]
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await clear_and_send(callback.message, text, keyboard, parse_mode="Markdown")

# --- Просмотр фильма ---
@router.callback_query(F.data.startswith("view:"))
async def view_movie(callback: CallbackQuery):
    """
    Показывает подробную карточку фильма.

    :param callback: Callback с ID фильма
    """
    await callback.answer()
    try:
        movie_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка: неверный ID")
        return

    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id)
    movie = next((m for m in movies if m["id"] == movie_id), None)

    if not movie:
        await clear_and_send(callback.message, "❌ Фильм не найден.", await get_main_menu_with_stats(user_id))
        return

    caption = f"🎥 *{movie['title']}*\n\n"
    caption += f"🎭 Жанр: {movie['genre']}\n\n"
    if movie["description"]:
        caption += f"📝 {movie['description']}\n\n"
    caption += f"📅 Добавлен: {movie['added_at'].split()[0]}"

    is_watched = bool(movie["watched"])
    mark_text = "↩️ Отметить как непросмотренное" if is_watched else "✅ Пометить как просмотренное"
    mark_cb = f"unwatch:{movie['id']}" if is_watched else f"watch:{movie['id']}"

    share_url = f"https://t.me/share/url?url=Посмотри%20этот%20фильм!&text={caption.replace(' ', '%20').replace('\n', '%0A')}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=mark_text, callback_data=mark_cb)],
        [InlineKeyboardButton(text="📤 Поделиться", url=share_url)],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{movie['id']}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="my_movies")]
    ])

    try:
        await callback.message.delete()
    except:
        pass

    if movie["poster_id"]:
        await callback.message.answer_photo(
            photo=movie["poster_id"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(caption, parse_mode="Markdown", reply_markup=keyboard)

# --- Отметка как просмотренное / непросмотренное ---
@router.callback_query(F.data.startswith("watch:"))
async def mark_as_watched(callback: CallbackQuery):
    """
    Отмечает фильм как просмотренный.

    :param callback: Callback с ID фильма
    """
    try:
        movie_id = int(callback.data.split(":", 1)[1])
    except:
        await callback.answer("❌ Ошибка ID", show_alert=True)
        return

    await mark_movie_watched(movie_id, callback.from_user.id, watched=True)
    await callback.answer("✅ Отмечено как просмотренное", show_alert=True)
    await view_movie(callback)

@router.callback_query(F.data.startswith("unwatch:"))
async def mark_as_unwatched(callback: CallbackQuery):
    """
    Отмечает фильм как непросмотренный.

    :param callback: Callback с ID фильма
    """
    try:
        movie_id = int(callback.data.split(":", 1)[1])
    except:
        await callback.answer("❌ Ошибка ID", show_alert=True)
        return

    await mark_movie_watched(movie_id, callback.from_user.id, watched=False)
    await callback.answer("↩️ Отмечено как непросмотренное", show_alert=True)
    await view_movie(callback)