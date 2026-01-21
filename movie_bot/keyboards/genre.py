"""
Генерация клавиатуры выбора жанра.
Поддерживает режимы: добавление, рекомендация, редактирование.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from movie_bot.utils.text_builder import TextBuilder

# ✅ Список жанров без иконок (чистые значения)
GENRES = ["Фильм", "Сериал", "Аниме", "Мультфильм"]

# Конфигурация режимов
MODE_CONFIG = {
    "add": {
        "prefix": "add_genre",
        "cancel_text": TextBuilder.btn_cancel(),
        "cancel_callback": "back_main"
    },
    "rec": {
        "prefix": "rec_genre",
        "cancel_text": TextBuilder.btn_back(),
        "cancel_callback": "back_main"
    },
    "edit": {
        "prefix": "edit_genre",
        "cancel_text": "⬅️ Назад",
        "cancel_callback": "back_to_edit"
    }
}


def get_genre_keyboard(mode: str = "add") -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с выбором жанра.

    :param mode: 'add', 'rec', 'edit'
    :return: Inline-клавиатура
    """
    config = MODE_CONFIG.get(mode, MODE_CONFIG["add"])

    keyboard = []

    # Жанры
    for genre in GENRES:
        text = TextBuilder.genre_button_text(genre)  # Добавляем иконку только в текст
        callback_data = f"{config['prefix']}:{genre}"  # Только чистое название
        keyboard.append([
            InlineKeyboardButton(text=text, callback_data=callback_data)
        ])

    # Кнопка отмены
    keyboard.append([
        InlineKeyboardButton(
            text=config["cancel_text"],
            callback_data=config["cancel_callback"]
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)