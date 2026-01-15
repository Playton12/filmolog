"""
Вспомогательные функции.

Содержит:
- clear_and_send — удаление старого и отправка нового сообщения
- get_similar_movies — fuzzy-сравнение названий
"""

from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fuzzywuzzy import fuzz

async def clear_and_send(message: Message, text: str, keyboard, parse_mode=None):
    """
    Удаляет старое сообщение и отправляет новое.

    Используется для "перерисовки" интерфейса без спама.

    :param message: Старое сообщение (будет удалено)
    :param text: Текст нового сообщения
    :param keyboard: Клавиатура (InlineKeyboardMarkup)
    :param parse_mode: 'Markdown' или 'HTML'
    """
    try:
        await message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    await message.answer(text, reply_markup=keyboard, parse_mode=parse_mode)

def get_similar_movies(movies: list, title: str, threshold: int = 75):
    """
    Находит фильмы с похожими названиями с помощью fuzzy-поиска.

    Использует:
    - fuzz.ratio — прямое сравнение
    - fuzz.token_sort_ratio — сравнение с учётом порядка слов

    :param movies: Список фильмов (с полем 'title')
    :param title: Введённое пользователем название
    :param threshold: Минимальная схожесть (0–100)
    :return: Список похожих фильмов (в порядке убывания схожести)
    """
    similar = []
    for movie in movies:
        ratio1 = fuzz.ratio(title.lower(), movie["title"].lower())
        ratio2 = fuzz.token_sort_ratio(title.lower(), movie["title"].lower())
        similarity = max(ratio1, ratio2)
        if threshold <= similarity < 100:
            similar.append({"movie": movie, "similarity": similarity})
    similar.sort(key=lambda x: x["similarity"], reverse=True)
    return [item["movie"] for item in similar]

def get_movie_card_text(movie: dict) -> str:
    """
    Генерирует красивый текст-карточку фильма.

    :param movie: Словарь с полями фильма (title, genre, description, poster_id, watched)
    :return: Форматированный текст
    """
    title = movie.get("title", "Без названия")
    genre = movie.get("genre", "Не указан")
    description = movie.get("description", "Нет описания")

    # Обрезаем описание, если длинное
    if len(description) > 120:
        description = description[:117] + "..."

    return (
        f"🎬 <b>{title}</b>\n"
        f"🧩 <b>Жанр:</b> {genre}\n"
        f"📝 <b>Описание:</b> {description}"
    )