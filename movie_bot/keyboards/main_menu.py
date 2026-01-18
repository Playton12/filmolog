"""
Клавиатура главного меню с красивой статистикой.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from movie_bot.database.queries import get_all_movies


async def get_main_menu_with_stats(user_id: int) -> InlineKeyboardMarkup:
    """
    Возвращает главное меню с красивой статистикой.
    """
    movies = await get_all_movies(user_id=user_id, watched=None)
    total = len(movies)
    watched = len([m for m in movies if m["watched"]])

    # Прогресс-бар
    if total > 0:
        progress = (watched / total) * 100
        filled = int(progress // 10)
        bar = "🟩" * filled + "◽️" * (10 - filled)
        progress_str = f"\n\n📊 Прогресс: {bar} {int(progress)}%"
    else:
        progress_str = ""

    # Текст статистики
    if total == 0:
        stats_text = "📭 Пока пусто"
    elif total == 1:
        stats_text = "🎬 1 фильм в вашей библиотеке"
    else:
        stats_text = f"📚 {total} фильмов | ✅ {watched} просмотрено"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add")],
        [InlineKeyboardButton(text="🎯 Рекомендаии", callback_data="recommend")],
        [InlineKeyboardButton(text="📂 Мой контент", callback_data="my_movies")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])

    return keyboard