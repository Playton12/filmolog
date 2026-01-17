"""
Вспомогательные функции.
"""

from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fuzzywuzzy import fuzz
from datetime import datetime
import logging

async def clear_and_send(message_or_callback, text: str, reply_markup=None, parse_mode=None):
    """
    Универсально удаляет предыдущее сообщение и отправляет новое.
    Работает с Message и CallbackQuery.
    """
    bot = None
    chat_id = None

    try:
        if isinstance(message_or_callback, CallbackQuery):
            msg = message_or_callback.message
            bot = msg.bot
            chat_id = msg.chat.id
            await msg.delete()
            await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        elif isinstance(message_or_callback, Message):
            bot = message_or_callback.bot
            chat_id = message_or_callback.chat.id
            await message_or_callback.delete()
            await message_or_callback.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            bot = message_or_callback.bot
            chat_id = message_or_callback.from_user.id
            await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logging.warning(f"[clear_and_send] Ошибка: {e}")
        try:
            await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e2:
            logging.error(f"[clear_and_send] Фатальная ошибка: {e2}")


def get_similar_movies(movies: list, title: str, threshold: int = 75):
    """
    Находит фильмы с похожими названиями с помощью fuzzy-поиска.
    """
    similar = []
    for movie in movies:
        ratio1 = fuzz.ratio(title.lower(), movie["title"].lower())
        ratio2 = fuzz.token_sort_ratio(title.lower(), movie["title"].lower())
        similarity = max(ratio1, ratio2)
        if threshold <= similarity < 100:
            similar.append({"movie": movie, "similarity": similarity})
    similar.sort(key=lambda x: x["similarity"], reverse=True)
    return [item["movie"]["title"] for item in similar]


def format_date(iso_date: str) -> str:
    """
    Форматирует ISO-дату в читаемый вид: 17.01.2025
    """
    if not iso_date:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except:
        return "ошибка даты"


def get_movie_card_text(movie: dict) -> str:
    """
    Возвращает красиво отформатированную карточку фильма.
    """
    lines = []

    # 🎬 Заголовок
    lines.append(f"🎬 <b>{movie['title']}</b>")
    lines.append("")

    # 🎭 Жанр
    lines.append(f"🎭 <b>Жанр:</b> <i>{movie['genre']}</i>")
    lines.append("")

    # 📝 Описание
    description = movie["description"] or "Описание отсутствует."
    if len(description) > 200:
        description = description[:197] + "..."
    lines.append(f"📝 <b>Описание:</b>")
    lines.append(f"<i>{description}</i>")
    lines.append("")

    # 📅 Даты
    added_at = movie.get("added_at")
    watched_at = movie.get("watched_at")
    watched = movie["watched"]

    lines.append(f"📌 <b>Добавлен:</b> <i>{format_date(added_at)}</i>")

    if watched and watched_at:
        lines.append(f"✅ <b>Просмотрен:</b> <i>{format_date(watched_at)}</i>")
    elif watched:
        lines.append("✅ <b>Просмотрен:</b> <i>Дата неизвестна</i>")
    else:
        lines.append("⭕ <b>Статус:</b> <i>не просмотрен</i>")

    return "\n".join(lines)