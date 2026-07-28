from typing import List, Union, Optional
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest  # ← Единственное исключение, которое нужно
)
from thefuzz import fuzz
import logging

logger = logging.getLogger(__name__)


async def clear_and_send(
    event: Union[Message, CallbackQuery, Bot],
    text: str,
    reply_markup=None,
    parse_mode: Optional[str] = None
):
    """
    Универсально удаляет предыдущее сообщение и отправляет новое.
    Обрабатывает:
    - Сообщение уже удалено
    - Flood limit (Too Many Requests)
    - Пользователь заблокировал бота
    """
    bot: Optional[Bot] = None
    chat_id: Optional[int] = None
    message_to_delete: Optional[Message] = None

    try:
        if isinstance(event, CallbackQuery):
            message_to_delete = event.message
            bot = message_to_delete.bot
            chat_id = message_to_delete.chat.id
        elif isinstance(event, Message):
            message_to_delete = event
            bot = event.bot
            chat_id = event.chat.id
        elif isinstance(event, Bot):
            # Режим: просто отправить (например, из health-check)
            logger.warning("clear_and_send получил Bot — удаление невозможно")
            return
        else:
            return

        # Попытка удалить сообщение
        if message_to_delete:
            try:
                await message_to_delete.delete()
            except TelegramBadRequest as e:
                error_msg = str(e).lower()
                if "message to delete not found" in error_msg:
                    pass  # Нормально — сообщение уже удалено
                elif "message can't be deleted" in error_msg:
                    pass  # Бот не может удалить (например, старое сообщение)
                else:
                    logger.debug(f"[clear_and_send] Неизвестная ошибка удаления: {e}")

        # Отправка нового сообщения
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    except TelegramForbiddenError:
        # Пользователь заблокировал бота
        logger.debug(f"Бот заблокирован пользователем {chat_id}")
        pass
    except TelegramBadRequest as e:
        error_msg = str(e).lower()
        if "retry after" in error_msg:
            # Flood control: Too Many Requests
            logger.warning(f"Flood limit: попробуйте позже — {e}")
            # В продакшене можно поставить sleep, но здесь — просто игнор
        elif "message is too long" in error_msg:
            logger.error("Сообщение слишком длинное")
        else:
            logger.error(f"TelegramBadRequest при отправке: {e}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка в clear_and_send: {e}", exc_info=True)
        # Фолбэк — редкий случай
        try:
            if bot and chat_id:
                await bot.send_message(chat_id, "🔄 Повторная попытка...")
        except:
            pass



def get_similar_movies(movies, query: str, threshold: int = 75) -> List[str]:
    """
    Возвращает список похожих названий фильмов с помощью fuzzy-поиска.

    :param movies: Список фильмов с полем 'title'
    :param query: Поисковый запрос
    :param threshold: Порог схожести (0–100)
    :return: Список названий, отсортированных по релевантности
    """
    query = query.lower().strip()
    matches = []

    for movie in movies:
        title = str(movie["title"]).lower().strip()
        similarity = fuzz.ratio(query, title)
        if similarity >= threshold:
            matches.append(movie["title"])  # Сохраняем оригинальное название

    # Сортируем по убыванию схожести
    return sorted(matches, key=lambda x: -fuzz.ratio(query, x.lower()))