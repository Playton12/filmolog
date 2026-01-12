"""
Состояния для машины состояний (FSM).

Определяет пошаговые сценарии:
- Добавление фильма
- Редактирование
- Пользовательские состояния
"""

from aiogram.fsm.state import StatesGroup, State


class AddMovie(StatesGroup):
    """Состояния для добавления нового фильма."""
    title = State()
    genre = State()
    description = State()
    poster = State()


class EditMovie(StatesGroup):
    """Состояния для редактирования фильма."""
    title = State()
    genre = State()
    description = State()
    poster = State()


class UserStates(StatesGroup):
    """Глобальные состояния пользователя."""
    started = State()