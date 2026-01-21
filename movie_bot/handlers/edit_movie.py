"""
Обработчики редактирования фильма.
Теперь с использованием KeyboardFactory, TextBuilder и единым стилем.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from movie_bot.fsm import EditMovie  
from movie_bot.keyboards.factory import KeyboardFactory
from movie_bot.database import get_movie_by_id, update_movie, get_all_movies 
from movie_bot.utils.helpers import get_similar_movies, clear_and_send
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.text_builder import TextBuilder
from movie_bot.keyboards.factory import KeyboardFactory

router = Router()
logger = logging.getLogger(__name__)

# --- Отображение полей и иконки ---
FIELD_DISPLAY = {
    "title": "Название",
    "genre": "Жанр",
    "description": "Описание",
    "poster_id": "Постер"
}

FIELD_ICONS = {
    "title": "📝",
    "genre": "🎭",
    "description": "📄",
    "poster_id": "🖼"
}

@router.callback_query(F.data.startswith("edit_select:"))
async def edit_select_movie(callback: CallbackQuery, state: FSMContext):
    try:
        movie_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        movie = await get_movie_by_id(user_id, movie_id)
        if not movie:
            await callback.answer("❌ Фильм не найден.", show_alert=True)
            return

        await state.update_data(movie_id=movie_id, movie=dict(movie))
        await clear_and_send(
            callback.message,
            f"🔧 Редактирование: <b>{movie['title']}</b>\n\nВыберите поле:",
            KeyboardFactory.edit_menu(),
            parse_mode="HTML"
        )
        await state.set_state(EditMovie.title)
        await callback.answer()
    except Exception as e:
        logger.error(f"[edit_movie] Ошибка при выборе фильма: {e}")
        await callback.message.answer("❌ Ошибка при открытии редактирования.")
        await state.clear()


@router.callback_query(EditMovie.title, F.data.startswith("edit_field:"))
async def edit_choose_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":", 1)[1]
    if field not in FIELD_DISPLAY:
        await callback.answer("❌ Неизвестное поле.", show_alert=True)
        return

    await state.update_data(edit_field=field)

    match field:
        case "title":
            await state.set_state(EditMovie.title)
            await clear_and_send(
                callback.message,
                TextBuilder.edit_enter_new_value("название"),
                KeyboardFactory.back_edit(),
                parse_mode="HTML"
            )
        case "genre":
            await state.set_state(EditMovie.genre)
            await clear_and_send(
                callback.message,
                "🎭 Выберите новый жанр",
                KeyboardFactory.genre("edit"),
                parse_mode="HTML"
            )
        case "description":
            await state.set_state(EditMovie.description)
            await clear_and_send(
                callback.message,
                TextBuilder.edit_enter_new_value("описание"),
                KeyboardFactory.back_edit(),
                parse_mode="HTML"
            )
        case "poster_id":
            await state.set_state(EditMovie.poster)
            await clear_and_send(
                callback.message,
                "🖼 Пришлите новый постер или нажмите «Пропустить»",
                KeyboardFactory.skip_poster_edit(),
                parse_mode="HTML"
            )
    await callback.answer()


@router.message(EditMovie.title)
async def edit_title(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer(TextBuilder.err_title_empty(), reply_markup=KeyboardFactory.back_edit())
        return

    user_input = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    movie_id = data["movie_id"]
    movie = await get_movie_by_id(user_id, movie_id)
    current_title = movie["title"]

    if user_input.lower() == current_title.lower():
        await message.answer("⚠️ Новое название совпадает с текущим.", reply_markup=KeyboardFactory.back_edit())
        return

    user_movies = await get_all_movies(user_id=user_id, watched=None)
    similar_list = get_similar_movies(user_movies, user_input, threshold=75)
    best_match = similar_list[0] if similar_list else None

    if best_match and user_input.lower() != best_match.lower():
        await state.update_data(new_title=user_input)
        kb = KeyboardFactory.confirmation(
            yes_callback=f"edit_correct:{best_match}",
            no_callback="edit_skip_correct"
        )
        await message.answer(
            TextBuilder.suggest_correction(input=user_input, match=best_match),
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    await ask_edit_confirmation(message, state, "title", user_input)


@router.callback_query(F.data.startswith("edit_correct:"))
async def edit_correct_title(callback: CallbackQuery, state: FSMContext):
    corrected = callback.data.split(":", 1)[1]
    await ask_edit_confirmation(callback, state, "title", corrected)
    await callback.answer()


@router.callback_query(F.data == "edit_skip_correct")
async def edit_skip_correction(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_input = data.get("new_title")
    if not user_input:
        await callback.message.answer("❌ Не удалось восстановить введённое название.")
        await state.clear()
        await callback.answer()
        return
    await ask_edit_confirmation(callback, state, "title", user_input)
    await callback.answer()


@router.callback_query(EditMovie.genre, F.data.startswith("edit_genre:"))
async def edit_genre(callback: CallbackQuery, state: FSMContext):
    new_genre = callback.data.split(":", 1)[1]
    from movie_bot.keyboards.genre import GENRES  # ✅ Локальный импорт
    if new_genre not in GENRES:
        await callback.answer("❌ Некорректный жанр.", show_alert=True)
        return
    await ask_edit_confirmation(callback, state, "genre", new_genre)
    await callback.answer()


@router.message(EditMovie.description)
async def edit_description(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer(TextBuilder.err_description_empty(), reply_markup=KeyboardFactory.back_edit())
        return
    await ask_edit_confirmation(message, state, "description", message.text.strip())


@router.message(EditMovie.poster, F.photo)
async def edit_poster_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await ask_edit_confirmation(message, state, "poster_id", file_id)


@router.callback_query(EditMovie.poster, F.data == "skip_poster")
async def edit_skip_poster(callback: CallbackQuery, state: FSMContext):
    await ask_edit_confirmation(callback, state, "poster_id", None)
    await callback.answer()


@router.callback_query(F.data == "back_to_edit")
async def back_to_edit_fields(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    movie = data.get("movie")
    if not movie:
        await callback.message.answer("❌ Сессия устарела.")
        await state.clear()
        await callback.answer()
        return

    # ✅ Исправлено: KeyboardFactory.edit_menu()
    await clear_and_send(
        callback.message,
        f"🔧 Редактирование: <b>{movie['title']}</b>\n\nВыберите поле:",
        KeyboardFactory.edit_menu()
,
        parse_mode="HTML"
    )
    await state.set_state(EditMovie.title)
    await callback.answer()


async def ask_edit_confirmation(message_or_callback, state: FSMContext, field: str, new_value):
    if isinstance(message_or_callback, CallbackQuery):
        message = message_or_callback.message
        user_id = message_or_callback.from_user.id
    else:
        message = message_or_callback
        user_id = message_or_callback.from_user.id

    data = await state.get_data()
    movie_id = data.get("movie_id")
    if not movie_id:
        await clear_and_send(message, "❌ Сессия устарела.", (await get_main_menu_with_stats(user_id))[1])
        await state.clear()
        return

    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await clear_and_send(message, "❌ Фильм не найден.", (await get_main_menu_with_stats(user_id))[1])
        await state.clear()
        return

    def format_value(val):
        if field == "poster_id":
            return "🖼 Есть" if val else "❌ Нет"
        return str(val) if val else "❌ Пусто"

    old_display = format_value(movie.get(field))
    new_display = format_value(new_value)
    field_name = FIELD_DISPLAY[field]
    icon = FIELD_ICONS[field]

    text = TextBuilder.confirm_edit_field(
        field_name=field_name,
        icon=icon,
        old_value=old_display,
        new_value=new_display
    )

    kb = KeyboardFactory.confirmation(
        yes_callback="confirm_edit:yes",
        no_callback="confirm_edit:no"
    )

    try:
        if isinstance(message_or_callback, CallbackQuery):
            await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"[edit_movie] Ошибка отправки подтверждения: {e}")
        await message.answer("❌ Ошибка интерфейса. Начните сначала.")
        await state.clear()
        return

    await state.update_data(
        pending_edit={
            "field": field,
            "value": new_value,
            "field_name": field_name,
            "old_display": old_display,
            "new_display": new_display
        }
    )
    await state.set_state(EditMovie.confirm)

@router.callback_query(EditMovie.confirm, F.data == "confirm_edit:yes")
async def confirm_edit_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending = data["pending_edit"]
    movie_id = data["movie_id"]
    user_id = callback.from_user.id

    try:
        await update_movie(user_id, movie_id, **{pending["field"]: pending["value"]})
        logger.info(f"Пользователь {user_id} обновил поле '{pending['field']}' фильма {movie_id}")
    except Exception as e:
        logger.error(f"[edit] Ошибка при обновлении фильма {movie_id}: {e}")
        await callback.message.answer("❌ Ошибка при сохранении.")
        await state.clear()
        return

    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await clear_and_send(callback.message, "❌ Фильм не найден.", (await get_main_menu_with_stats(user_id))[1])
        await state.clear()
        return

    text = TextBuilder.success_edit_field(
        field_name=pending["field_name"],
        old_value=pending["old_display"],
        new_value=pending["new_display"]
    ) + "\n\n" + TextBuilder.movie_card(movie)

    await clear_and_send(
        callback.message,
        text,
        KeyboardFactory.edit_menu(),
        parse_mode="HTML"
    )
    await state.set_state(EditMovie.title)
    await callback.answer()


@router.callback_query(EditMovie.confirm, F.data == "confirm_edit:no")
async def confirm_edit_no(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    movie = await get_movie_by_id(callback.from_user.id, data["movie_id"])
    text = "❌ Изменение отменено.\n\n" + TextBuilder.movie_card(movie)
    await clear_and_send(callback.message, text, KeyboardFactory.edit_menu()
, parse_mode="HTML")
    await state.set_state(EditMovie.title)
    await callback.answer()


@router.callback_query(F.data == "edit_done")
async def edit_done(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    movie = await get_movie_by_id(user_id, data["movie_id"])

    if not movie:
        await clear_and_send(callback.message, "❌ Фильм не найден.", (await get_main_menu_with_stats(user_id))[1])
        await state.clear()
        await callback.answer()
        return

    await state.clear()

    # ✅ Исправлено: TextBuilder.movie_card
    text = "✅ Редактирование завершено.\n\n" + TextBuilder.movie_card(movie)
    keyboard = (await get_main_menu_with_stats(user_id))[1]

    await clear_and_send(callback.message, text, keyboard, parse_mode="HTML")
    await callback.answer()