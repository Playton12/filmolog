"""Обработчики Telegram-бота."""
"""
Автоматически импортирует все роутеры из handlers.
"""
from .start import router as start_router
from .add_movie import router as add_movie_router
from .recommend import router as recommend_router
from .my_movies import router as my_movies_router
from .help import router as help_router
from .restart import router as restart_router

__all__ = [
    "start_router",
    "add_movie_router",
    "recommend_router",
    "my_movies_router",
    "help_router",
    "restart_router",
]