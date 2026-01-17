from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.fsm.states import UserStates
from movie_bot.database.queries import get_all_movies

router = Router()

@router.message(F.text == "/restart")
async def cmd_restart(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserStates.started)

    user_id = message.from_user.id
    all_movies = await get_all_movies(user_id=user_id, watched=None)
    total = len(all_movies)
    watched = len([m for m in all_movies if m["watched"]])

    if total == 0:
        stats_text = "📭 У вас пока нет фильмов."
    else:
        stats_text = (f"📊 Ваши фильмы: <b>{watched}/{total}</b>\n"
                      f"✅ Просмотрено — {watched}, "
                      f"🆕 В ожидании — {total - watched}")

    text = f"🔄 Бот перезапущен.\n\n{stats_text}"
    keyboard = await get_main_menu_with_stats(user_id)

    await clear_and_send(
        message,
        text,
        keyboard,
        parse_mode="HTML"
    )