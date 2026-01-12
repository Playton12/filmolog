"""
Обработчики команды /start и главного меню.

Функции:
- cmd_start — приветствие и отображение меню
- back_to_main — возврат в главное меню
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.fsm.states import UserStates

router = Router()
"""Router для команды /start и кнопки «Назад»."""

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.

    Отображает приветствие и главное меню.

    :param message: Входящее сообщение
    :param state: Контекст FSM
    """
    await state.set_state(UserStates.started)
    keyboard = await get_main_menu_with_stats(message.from_user.id)
    await message.answer("👋 Привет! Я — бот для подбора фильмов.\nВыбери действие:", reply_markup=keyboard)

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки «Назад в меню».

    Очищает FSM и возвращает в главное меню.

    :param callback: Callback-запрос
    :param state: Контекст FSM
    """
    if await state.get_state():
        await state.clear()
    keyboard = await get_main_menu_with_stats(callback.from_user.id)
    await callback.message.edit_text("🔙 Вы в главном меню:", reply_markup=keyboard)
    await callback.answer()