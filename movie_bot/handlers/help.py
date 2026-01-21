"""
Обработчик команды /help.
Показывает описание всех функций бота с кнопкой возврата.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError

from movie_bot.keyboards.factory import KeyboardFactory
from movie_bot.utils.text_builder import TextBuilder

router = Router()
logger = logging.getLogger(__name__)

async def send_help(event, user_id: int):
    """
    Универсально отправляет справку — поддерживает Message и CallbackQuery.
    """
    text = TextBuilder.help_text()
    keyboard = KeyboardFactory.back_to_main()

    try:
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
        elif isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramForbiddenError:
        logger.warning(f"Бот заблокирован пользователем {user_id}. Не могу отправить /help.")
    except Exception as e:
        logger.error(f"[help] Ошибка при отправке справки пользователю {user_id}: {e}")
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Не удалось открыть справку.", show_alert=True)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обрабатывает команду /help.
    """
    await send_help(message, message.from_user.id)
    logger.info(f"Пользователь {message.from_user.id} вызвал /help")

@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """
    Обрабатывает нажатие кнопки "Помощь".
    """
    await send_help(callback, callback.from_user.id)
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} открыл помощь через кнопку")