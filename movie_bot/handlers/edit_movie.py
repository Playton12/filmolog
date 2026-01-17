from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import Router, F

from movie_bot.handlers.my_movies import send_movie_card
from movie_bot.fsm.states import EditMovie
from movie_bot.keyboards.genre import get_genre_keyboard, GENRES
from movie_bot.keyboards.utils import get_skip_poster_edit_button, get_back_edit_button
from movie_bot.database.queries import get_all_movies, get_movie_by_id, update_movie
from movie_bot.utils.helpers import get_similar_movies, clear_and_send, get_movie_card_text
from movie_bot.keyboards.main_menu import get_main_menu_with_stats

router = Router()

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
            await callback.message.answer("❌ Фильм не найден.")
            return

        await state.update_data(movie_id=movie_id, movie=movie)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data="edit_field:title")],
            [InlineKeyboardButton(text="🎭 Жанр", callback_data="edit_field:genre")],
            [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field:description")],
            [InlineKeyboardButton(text="🖼 Постер", callback_data="edit_field:poster")],
            [InlineKeyboardButton(text="✅ Готово", callback_data="edit_done")],
        ])

        await clear_and_send(
            callback.message,
            "🔧 Выберите поле для редактирования:\n\n" + get_movie_card_text(movie),
            keyboard,
            parse_mode="HTML"
        )
        await state.set_state(EditMovie.title)
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка: {e}")
        await state.clear()


@router.callback_query(EditMovie.title, F.data.startswith("edit_field:"))
async def edit_choose_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":")[1]
    await state.update_data(edit_field=field)

    match field:
        case "title":
            await state.set_state(EditMovie.title)
            await clear_and_send(callback.message, f"✏️ Введите новое {FIELD_DISPLAY[field]}:", get_back_edit_button())
        case "genre":
            await state.set_state(EditMovie.genre)
            await clear_and_send(callback.message, "🎭 Выберите новый жанр", get_genre_keyboard("edit"))
        case "description":
            await state.set_state(EditMovie.description)
            await clear_and_send(callback.message, f"✏️ Введите новое {FIELD_DISPLAY[field]}:", get_back_edit_button())
        case "poster":
            await state.set_state(EditMovie.poster)
            await clear_and_send(callback.message, "🖼 Пришлите фото постера или выберите «Без постера»", get_skip_poster_edit_button())
    await callback.answer()


@router.message(EditMovie.title)
async def edit_title(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("❌ Название не может быть пустым.", reply_markup=get_back_edit_button())
        return

    user_input = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    movie_id = data["movie_id"]
    movie = await get_movie_by_id(user_id, movie_id)
    current_title = movie["title"]

    if user_input.lower() == current_title.lower():
        await message.answer("⚠️ Новое название совпадает с текущим.", reply_markup=get_back_edit_button())
        return

    user_movies = await get_all_movies(user_id=user_id, watched=False)
    similar_list = get_similar_movies(user_movies, user_input, threshold=75)
    best_match = similar_list[0] if similar_list else None

    if best_match and user_input.lower() != best_match.lower():
        await state.update_data(new_title=user_input)
        await message.answer(
            f"🔍 Возможно, вы имели в виду: *{best_match}*?\n\nВы написали: *{user_input}*\n\nИсправить?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data=f"edit_correct:{best_match}")],
                [InlineKeyboardButton(text="❌ Нет", callback_data="edit_skip_correct")],
            ]),
            parse_mode="Markdown"
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
    if new_genre not in GENRES:
        await callback.answer("❌ Некорректный жанр.", show_alert=True)
        return
    await ask_edit_confirmation(callback, state, "genre", new_genre)
    await callback.answer()


@router.message(EditMovie.description)
async def edit_description(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("❌ Описание не может быть пустым.", reply_markup=get_back_edit_button())
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="edit_field:title")],
        [InlineKeyboardButton(text="🎭 Жанр", callback_data="edit_field:genre")],
        [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field:description")],
        [InlineKeyboardButton(text="🖼 Постер", callback_data="edit_field:poster")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="edit_done")],
    ])

    await clear_and_send(
        callback.message,
        "🔧 Выберите поле для редактирования:\n\n" + get_movie_card_text(movie),
        keyboard,
        parse_mode="HTML"
    )
    await state.set_state(EditMovie.title)
    await callback.answer()


async def ask_edit_confirmation(message_or_callback, state: FSMContext, field: str, new_value):
    if isinstance(message_or_callback, CallbackQuery):
        from_user = message_or_callback.from_user
        message = message_or_callback.message
        bot = message_or_callback.bot
    elif isinstance(message_or_callback, Message):
        from_user = message_or_callback.from_user
        message = message_or_callback
        bot = message_or_callback.bot
    else:
        await state.clear()
        return

    user_id = from_user.id

    if from_user.is_bot:
        print(f"[SECURITY] Бот (ID: {user_id}) пытается редактировать фильм")
        try:
            await message_or_callback.answer("❌ Действие недоступно для ботов.")
        except:
            pass
        return

    data = await state.get_data()
    movie_id = data.get("movie_id")
    if not movie_id:
        await clear_and_send(
            message_or_callback,
            "❌ Сессия устарела. Начните сначала.",
            await get_main_menu_with_stats(user_id)
        )
        await state.clear()
        return

    try:
        movie_id = int(movie_id)
    except (ValueError, TypeError):
        await clear_and_send(
            message_or_callback,
            "❌ Некорректный ID фильма.",
            await get_main_menu_with_stats(user_id)
        )
        await state.clear()
        return

    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await clear_and_send(
            message_or_callback,
            "❌ Фильм не найден.",
            await get_main_menu_with_stats(user_id)
        )
        await state.clear()
        return

    def format_value(val, fld: str):
        if fld == "poster_id":
            return "🖼 Есть" if val else "❌ Нет"
        return str(val) if val else "❓ Не задано"

    old_value = movie.get(field)
    old_display = format_value(old_value, field)
    new_display = format_value(new_value, field)
    field_name = FIELD_DISPLAY[field]
    icon = FIELD_ICONS.get(field, "🔧")

    text = (
        f"{icon} *Подтвердите изменение*\n\n"
        f"🗂 Поле: *{field_name}*\n"
        f"🔄 Старое: `{old_display}`\n"
        f"✅ Новое: `{new_display}`\n\n"
        f"Сохранить изменения?"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, сохранить", callback_data="confirm_edit:yes")],
        [InlineKeyboardButton(text="⬅️ Нет, назад", callback_data="confirm_edit:no")]
    ])

    try:
        if isinstance(message_or_callback, CallbackQuery):
            await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        error_msg = "✉️ Чтобы продолжить, напишите боту в личку: [открыть](t.me/ваш_бот) \n\nПосле — нажмите /start"
        try:
            await bot.send_message(user_id, error_msg, disable_web_page_preview=True)
        except:
            pass
        await state.clear()
        return

    await state.update_data(
        pending_edit={
            "field": field,
            "value": new_value,
            "old_display": old_display,
            "new_display": new_display,
            "field_name": field_name
        }
    )
    await state.set_state(EditMovie.confirm)


@router.callback_query(EditMovie.confirm, F.data == "confirm_edit:yes")
async def confirm_edit_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending = data.get("pending_edit")
    movie_id = data["movie_id"]
    user_id = callback.from_user.id

    if not pending:
        await callback.message.answer("❌ Ошибка: нет данных для сохранения.")
        await state.clear()
        return

    field, new_value = pending["field"], pending["value"]
    await update_movie(user_id, movie_id, **{field: new_value})

    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await clear_and_send(callback.message, "❌ Фильм не найден.", await get_main_menu_with_stats(user_id))
        await state.clear()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="edit_field:title")],
        [InlineKeyboardButton(text="🎭 Жанр", callback_data="edit_field:genre")],
        [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field:description")],
        [InlineKeyboardButton(text="🖼 Постер", callback_data="edit_field:poster")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="edit_done")],
    ])

    change_text = (
        f"✅ *Поле обновлено*\n\n"
        f"🗂 {pending['field_name']}:\n"
        f"➡️ `{pending['old_display']}` → `{pending['new_display']}`\n\n"
    )

    await clear_and_send(
        callback.message,
        change_text + get_movie_card_text(movie),
        keyboard,
        parse_mode="HTML"
    )
    await state.set_state(EditMovie.title)
    await callback.answer()


@router.callback_query(F.data == "edit_done")
async def edit_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    movie_id = data.get("movie_id")
    user_id = callback.from_user.id

    if not movie_id:
        await clear_and_send(
            callback.message,
            "❌ Сессия устарела.",
            await get_main_menu_with_stats(user_id)
        )
        await state.clear()
        await callback.answer()
        return

    # Проверим, что фильм существует
    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await clear_and_send(
            callback.message,
            "❌ Фильм не найден.",
            await get_main_menu_with_stats(user_id)
        )
        await state.clear()
        await callback.answer()
        return

    # Очищаем FSM
    await state.clear()

    # Показываем карточку фильма
    await send_movie_card(callback, movie_id)  # ✅ Вызываем универсальную функцию

    # Уже внутри send_movie_card будет callback.answer()



@router.callback_query(EditMovie.confirm, F.data == "confirm_edit:no")
async def confirm_edit_no(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    movie_id = data["movie_id"]
    user_id = callback.from_user.id
    movie = await get_movie_by_id(user_id, movie_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="edit_field:title")],
        [InlineKeyboardButton(text="🎭 Жанр", callback_data="edit_field:genre")],
        [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field:description")],
        [InlineKeyboardButton(text="🖼 Постер", callback_data="edit_field:poster")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="edit_done")],
    ])

    await clear_and_send(
        callback.message,
        "❌ Изменение отменено.\n\n" + get_movie_card_text(movie),
        keyboard,
        parse_mode="HTML"
    )
    await state.set_state(EditMovie.title)
    await callback.answer()