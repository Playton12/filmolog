"""
Вспомогательные функции для генерации клавиатур.

Содержит:
- Кнопки «Отмена», «Назад»
- Кнопка «Пропустить постер»
- Генерация списка фильмов
"""

from movie_bot.keyboards.genre import GENRES
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cancel_button():
    """
    Кнопка «Отмена» — возвращает в главное меню.

    :return: Клавиатура с одной кнопкой
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]
    ])
    
def get_back_edit_button():
    """
    Клавиатура с одной кнопкой «Назад» — возвращается к выбору полей.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_edit")]
    ])

def get_back_button():
    """
    Кнопки «Назад» и «Отмена» — для возврата на предыдущий шаг.

    :return: Клавиатура с двумя кнопками
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙Назад", callback_data="back_step")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]
    ])

def get_skip_poster_button():
    """Клавиатура для редактирования постера"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Без постера", callback_data="skip_poster")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_step")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]
    ])

def get_skip_poster_edit_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Без постера", callback_data="skip_poster")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_edit")]
    ])

def get_movies_keyboard(movies, action="delete"):
    """
    Генерирует список фильмов как кнопки.

    :param movies: Список фильмов (с полем 'title' и 'id')
    :param action: Действие при нажатии: 'delete', 'view' и т.д.
    :return: Inline-клавиатура
    """
    buttons = [[InlineKeyboardButton(text=f"🗑 {m['title']}", callback_data=f"{action}:{m['id']}")] for m in movies]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_genre_with_navigation():
    """
    Клавиатура с жанрами + две кнопки: Назад и Отмена.
    Используется при добавлении фильма.
    """
    keyboard = []
    for genre in GENRES:
        keyboard.append([InlineKeyboardButton(text=genre, callback_data=f"add_genre:{genre}")])
    keyboard.extend([
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_step")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)