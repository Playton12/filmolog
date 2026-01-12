"""
Генерация клавиатуры выбора жанра.

Поддерживает два режима:
- Добавление фильма
- Рекомендация
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

GENRES = ["Комедия", "Драма", "Боевик", "Фантастика"]
"""Список поддерживаемых жанров."""

def get_genre_keyboard(mode: str = "add") -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с выбором жанра.

    :param mode: Режим: 'add' — для добавления, 'rec' — для рекомендаций
    :return: Inline-клавиатура
    """
    prefix = "add_genre" if mode == "add" else "rec_genre"
    buttons = [[InlineKeyboardButton(text=genre, callback_data=f"{prefix}:{genre}")] for genre in GENRES]
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)