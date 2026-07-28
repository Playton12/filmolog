"""
Глобальный экземпляр бота.

Создаётся через create_bot(), а не при импорте модуля,
чтобы избежать побочных эффектов и Allow подмену для тестов.
"""
from aiogram import Bot

_bot: Bot | None = None


def create_bot(token: str) -> Bot:
    """Создаёт и кэширует экземпляр бота."""
    global _bot
    _bot = Bot(token=token)
    return _bot


def get_bot() -> Bot:
    """Возвращает созданный экземпляр бота."""
    if _bot is None:
        raise RuntimeError("Бот не инициализирован. Вызовите create_bot() перед использованием.")
    return _bot
