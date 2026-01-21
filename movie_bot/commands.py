"""
Управление командами бота.

Содержит:
- Список команд с описаниями
- Функцию установки команд через bot.set_my_commands
"""

from aiogram.types import BotCommand


# Список команд
BOT_COMMANDS = [
    ("restart", "🔄 Перезапустить"),
    ("add", "➕ Добавить"),
    ("recommend", "🎬 Рекомендации"),
    ("my_movies", "📂 Мой контент"),
    ("help", "ℹ️ Помощь"),
]


def get_commands() -> list[BotCommand]:
    """
    Возвращает список объектов BotCommand для регистрации в Telegram.
    """
    return [BotCommand(command=cmd, description=desc) for cmd, desc in BOT_COMMANDS]


def get_short_commands() -> str:
    """
    Возвращает строку с командами через запятую: '/add, ...'
    """
    return ", ".join([f"<code>/{cmd}</code>" for cmd, _ in BOT_COMMANDS])