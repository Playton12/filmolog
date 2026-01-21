"""
Обработчики команды /start и главного меню.

Функции:
- cmd_start — приветствие и отображение меню с статистикой
- back_to_main — возврат в главное меню с статистикой
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError

from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.utils.text_builder import TextBuilder

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Сбрасывает FSM и показывает главное меню с приветствием и статистикой.
    """
    user_id = message.from_user.id
    await state.clear()

    logger.info(f"Пользователь {user_id} запустил /start")

    await _send_main_menu(message, user_id, greeting=True)


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    """
    Обработчик кнопки «Назад в главное меню».
    Показывает главное меню с актуальной статистикой.
    """
    user_id = callback.from_user.id

    logger.info(f"Пользователь {user_id} вернулся в главное меню")

    await _send_main_menu(callback, user_id, greeting=False)
    await callback.answer()

async def _send_main_menu(event, user_id: int, greeting: bool = False):
    """
    Универсально отправляет главное меню с статистикой.
    :param event: Message или CallbackQuery
    :param user_id: ID пользователя
    :param greeting: Добавить приветствие
    """
    try:
        stats_text, keyboard = await get_main_menu_with_stats(user_id)

        if greeting:
            text = TextBuilder.start_greeting() + stats_text
        else:
            text = TextBuilder.main_menu_title() + stats_text

        await clear_and_send(event, text, keyboard, parse_mode="HTML")
    except TelegramForbiddenError:
        logger.warning(f"Бот заблокирован пользователем {user_id}. Не могу отправить главное меню.")
    except Exception as e:
        logger.error(f"[start] Ошибка при отправке главного меню для {user_id}: {e}")
        try:
            await clear_and_send(event, TextBuilder.start_failed(), None)
        except TelegramForbiddenError:
            pass  # Игнорируем, если не можем написать