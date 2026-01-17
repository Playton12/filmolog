"""
Генерация клавиатуры выбора жанра.

Поддерживает два режима:
- Добавление фильма
- Рекомендация
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

GENRES = ["Фильм", "Сериал", "Аниме", "Мультфильм"]
"""Список поддерживаемых жанров."""

def get_genre_keyboard(mode: str = "add") -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с выбором жанра.

    :param mode: Режим: 'add' — для добавления, 'rec' — для рекомендаций, 'edit' — для редактирования
    :return: Inline-клавиатура
    """
    if mode == "add":
        prefix = "add_genre"
        cancel_text = "❌ Отмена"
        cancel_callback = "back_main"
    elif mode == "rec":
        prefix = "rec_genre"
        cancel_text = "🔙 Назад"
        cancel_callback = "back_main"
    elif mode == "edit":
        prefix = "edit_genre"
        cancel_text = "🔙 Назад"
        cancel_callback = "back_to_edit"  # ✅ Возвращаемся к выбору полей
    else:
        prefix = "add_genre"
        cancel_text = "❌ Отмена"
        cancel_callback = "back_main"

    buttons = []
    for genre in GENRES:
        buttons.append([
            InlineKeyboardButton(
                text=genre,
                callback_data=f"{prefix}:{genre}"
            )
        ])

    # Кнопка "Назад" или "Отмена" в зависимости от режима
    buttons.append([
        InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback)
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)