"""
Обработчик команды /restart.
Сбрасывает FSM и возвращает в главное меню.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError

from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.utils.text_builder import TextBuilder

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext):
    """
    Перезапускает бот: очищает FSM и возвращает в главное меню.
    Поддерживает /restart и /restart@bot_username.
    """
    await state.clear()
    user_id = message.from_user.id

    logger.info(f"Пользователь {user_id} выполнил /restart")

    try:
        stats_text, keyboard = await get_main_menu_with_stats(user_id)
        text = f"✅ Сессия сброшена!\n\n{stats_text}"
        await clear_and_send(message, text, keyboard, parse_mode="HTML")
    except TelegramForbiddenError:
        logger.warning(f"Бот заблокирован пользователем {user_id}. Не могу отправить /restart.")
    except Exception as e:
        logger.error(f"[restart] Ошибка при /restart для {user_id}: {e}")
        try:
            await clear_and_send(message, TextBuilder.restart_failed(), None)
        except TelegramForbiddenError:
            pass  # Пользователь заблокировал бота