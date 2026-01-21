"""
Состояния FSM для бота управления фильмами.

Каждая группа — отдельный сценарий.
Имя состояния включает контекст (например, add_movie_title), чтобы избежать путаницы.
"""

from aiogram.fsm.state import StatesGroup, State


class AddMovie(StatesGroup):
    """
    Состояния сценария: добавление нового фильма.
    """
    title = State()
    genre = State()
    description = State()
    poster = State()


class EditMovie(StatesGroup):
    """
    Состояния сценария: редактирование существующего фильма.
    """
    title = State()
    genre = State()
    description = State()
    poster = State()
    confirm = State()


class MyMovies(StatesGroup):
    """
    Состояния для просмотра и поиска фильмов.
    """
    search_query = State()
    # pagination — зарезервировано (например, waiting_page)


class User(StatesGroup):
    """
    Глобальные состояния пользователя (если понадобятся).
    """
    # Пример: waiting_for_feedback, choosing_language
    pass


# Явный экспорт
__all__ = [
    "AddMovie",
    "EditMovie",
    "MyMovies",
    "User",
]