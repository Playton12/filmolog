"""
Обработчики для списка "Просмотрено".

Теперь использует ЕДИНУЮ карточку фильма из my_movies.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from movie_bot.database.queries import get_all_movies
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send

router = Router()


# --- Список просмотренных ---
@router.callback_query(F.data == "watched_list")
async def watched_list(callback: CallbackQuery):
    """
    Отображает список просмотренных фильмов.
    При клике — открывает общую карточку фильма.
    """
    await callback.answer()
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=True, order="added_at DESC")
    count = len(movies)

    if not movies:
        text = "📭 Вы пока ничего не посмотрели."
        keyboard = await get_main_menu_with_stats(user_id)
        await clear_and_send(callback.message, text, keyboard)
        return

    # Кнопки: каждый фильм → movie_info:{id}
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for movie in movies:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎥 {movie['title']}",
                callback_data=f"movie_info:{movie['id']}"
            )
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")
    ])

    text = f"✅ Просмотрено: *{count}* фильмов"
    await clear_and_send(callback.message, text, keyboard, parse_mode="Markdown")