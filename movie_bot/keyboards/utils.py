"""
Вспомогательные функции для генерации клавиатур.

Содержит:
- Кнопки «Отмена», «Назад»
- Кнопка «Пропустить постер»
- Генерация списка фильмов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cancel_button():
    """
    Кнопка «Отмена» — возвращает в главное меню.

    :return: Клавиатура с одной кнопкой
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_main")]
    ])

def get_back_button():
    """
    Кнопки «Назад» и «Отмена» — для возврата на предыдущий шаг.

    :return: Клавиатура с двумя кнопками
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_step")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_main")]
    ])

def get_skip_poster_button():
    """
    Кнопки для шага с постером: «Пропустить», «Назад», «Отмена».

    :return: Клавиатура
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_poster")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_step")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="back_main")]
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