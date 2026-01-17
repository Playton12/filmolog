"""
Обработчики команды /start и главного меню.

Функции:
- cmd_start — приветствие и отображение меню с статистикой
- back_to_main — возврат в главное меню с статистикой
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.database.queries import get_all_movies
from movie_bot.utils.helpers import clear_and_send
from movie_bot.fsm.states import UserStates
from movie_bot.utils.commands import get_short_commands

router = Router()
"""Router для команды /start и кнопки «Назад»."""


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.

    Отображает приветствие и главное меню с статистикой.
    
    :param message: Входящее сообщение
    :param state: Контекст FSM
    """
    user_id = message.from_user.id
    await state.set_state(UserStates.started)

    all_movies = await get_all_movies(user_id=user_id, watched=None)
    total = len(all_movies)
    watched = len([m for m in all_movies if m["watched"]])

    if total == 0:
        stats_text = "📭 У вас пока нет фильмов.\n\nДобавьте первый — нажмите «➕ Добавить фильм»"
    else:
        stats_text = (f"📊 Ваши фильмы: <b>{watched}/{total}</b>\n")

    text = f"👋 Привет! Я — бот для управления вашей библиотекой фильмов.\n\n{stats_text}"
    keyboard = await get_main_menu_with_stats(user_id)

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    """
    Обработчик кнопки «Назад в главное меню».

    Показывает главное меню с актуальной статистикой.
    
    :param callback: Callback-запрос
    """
    user_id = callback.from_user.id

    all_movies = await get_all_movies(user_id=user_id, watched=None)
    total = len(all_movies)
    watched = len([m for m in all_movies if m["watched"]])

    if total == 0:
        stats_text = "📭 У вас пока нет фильмов."
    else:
        stats_text = (f"📊 Ваши фильмы: <b>{watched}/{total}</b>\n")

    text = f"🏠 Главное меню\n\n{stats_text}"
    keyboard = await get_main_menu_with_stats(user_id)

    await clear_and_send(
        callback.message,
        text,
        keyboard,
        parse_mode="HTML"
    )
    await callback.answer()