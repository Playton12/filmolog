"""
Обработчики редактирования фильма.

Пошаговый сценарий:
1. Выбор фильма для редактирования
2. Выбор поля: Название / Жанр / Описание / Постер
3. Ввод нового значения (с проверками)
4. Сохранение в БД
"""

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import Router, F

from movie_bot.fsm.states import EditMovie
from movie_bot.keyboards.genre import get_genre_keyboard
from movie_bot.keyboards.utils import get_cancel_button, get_back_button, get_skip_poster_button, get_movies_keyboard
from movie_bot.database.queries import get_all_movies, get_movie_by_id, update_movie, is_movie_exists
from movie_bot.utils.helpers import get_similar_movies, clear_and_send
from movie_bot.keyboards.main_menu import get_main_menu_with_stats

router = Router()


@router.callback_query(F.data == "edit_menu")
async def edit_movie_start(callback: CallbackQuery, state: FSMContext):
    """
    Открывает меню выбора фильма для редактирования.
    Если фильмов нет — показывает подсказку.
    """
    user_id = callback.from_user.id
    movies = await get_all_movies(user_id=user_id, watched=False)
    
    if not movies:
        keyboard = await get_main_menu_with_stats(user_id)
        await clear_and_send(
            callback.message,
            "📭 У вас пока нет фильмов для редактирования.\n\n"
            "Сначала добавьте фильм — нажмите кнопку ниже 👇",
            keyboard
        )
        await callback.answer()
        return

    keyboard = get_movies_keyboard(movies, action="edit_select")
    await clear_and_send(
        callback.message,
        "✏️ Выберите фильм для редактирования:",
        keyboard
    )
    await callback.answer()


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

        from movie_bot.utils.helpers import get_movie_card_text

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
    """
    Переходит к редактированию выбранного поля.
    """
    field = callback.data.split(":")[1]
    field_names = {"title": "Название", "genre": "Жанр", "description": "Описание", "poster": "Постер"}
    await state.update_data(edit_field=field)

    if field == "title":
        await state.set_state(EditMovie.title)
        await clear_and_send(callback.message, f"✏️ Введите новое {field_names[field]}:", get_cancel_button())
    elif field == "genre":
        await state.set_state(EditMovie.genre)
        await clear_and_send(callback.message, f"🎭 Выберите новый {field_names[field]}", get_genre_keyboard("edit"))
    elif field == "description":
        await state.set_state(EditMovie.description)
        await clear_and_send(callback.message, f"✏️ Введите новое {field_names[field]}:", get_back_button())
    elif field == "poster":
        await state.set_state(EditMovie.poster)
        await clear_and_send(callback.message, "🖼 Пришлите новое фото постера или нажмите «Пропустить»", get_skip_poster_button())
    await callback.answer()


# --- Название ---
@router.message(EditMovie.title)
async def edit_title(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("❌ Название не может быть пустым.", reply_markup=get_cancel_button())
        return

    user_input = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    movie_id = data["movie_id"]
    current_title = (await get_movie_by_id(user_id, movie_id))["title"]

    user_movies = await get_all_movies(user_id=user_id, watched=False)
    similar_list = get_similar_movies(user_movies, user_input, threshold=75)
    best_match = similar_list[0]["movie"]["title"] if similar_list else None

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

    if user_input.lower() == current_title.lower():
        await message.answer("⚠️ Новое название совпадает с текущим.", reply_markup=get_cancel_button())
        return

    await ask_edit_confirmation(message, state, "title", user_input)


@router.callback_query(F.data.startswith("edit_correct:"))
async def edit_correct_title(callback: CallbackQuery, state: FSMContext):
    corrected = callback.data.split(":", 1)[1]
    await ask_edit_confirmation(callback.message, state, "title", corrected)
    await callback.answer()


@router.callback_query(F.data == "edit_skip_correct")
async def edit_skip_correction(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await ask_edit_confirmation(callback.message, state, "title", data["new_title"])
    await callback.answer()


# --- Жанр ---
@router.callback_query(EditMovie.genre, F.data.startswith("edit_genre:"))
async def edit_genre(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split(":", 1)[1]
    await ask_edit_confirmation(callback.message, state, "genre", genre)
    await callback.answer()


# --- Описание ---
@router.message(EditMovie.description)
async def edit_description(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("❌ Описание не может быть пустым.", reply_markup=get_back_button())
        return
    await ask_edit_confirmation(message, state, "description", message.text.strip())


# --- Постер ---
@router.message(EditMovie.poster, F.photo)
async def edit_poster_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await ask_edit_confirmation(message, state, "poster", file_id)


@router.callback_query(EditMovie.poster, F.data == "skip_poster")
async def edit_skip_poster(callback: CallbackQuery, state: FSMContext):
    await ask_edit_confirmation(callback.message, state, "poster", None)
    await callback.answer()


# === Вспомогательная функция ===
async def ask_edit_confirmation(message_or_callback, state: FSMContext, field: str, new_value):
    """
    Показывает пользователю старое и новое значение и спрашивает подтверждение.
    """
    data = await state.get_data()
    movie_id = data["movie_id"]
    user_id = message_or_callback.from_user.id

    current_movie = await get_movie_by_id(user_id, movie_id)
    if not current_movie:
        await clear_and_send(message_or_callback, "❌ Фильм не найден.", await get_main_menu_with_stats(user_id))
        await state.clear()
        return

    field_names = {
        "title": "Название",
        "genre": "Жанр",
        "description": "Описание",
        "poster": "Постер"
    }

    old_value = current_movie[field]
    if field == "poster":
        old_display = "есть" if old_value else "нет"
        new_display = "есть" if new_value else "нет"
    else:
        old_display = old_value or "не задано"
        new_display = new_value

    text = (
        f"🔍 Подтвердите изменение:\n\n"
        f"🗂 Поле: *{field_names[field]}*\n"
        f"🔄 Старое: `{old_display}`\n"
        f"✅ Новое: `{new_display}`\n\n"
        f"Сохранить изменения?"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, сохранить", callback_data="confirm_edit:yes")],
        [InlineKeyboardButton(text="⬅️ Нет, назад", callback_data="confirm_edit:no")]
    ])

    await clear_and_send(
        message_or_callback,
        text,
        keyboard,
        parse_mode="Markdown"
    )
    await state.update_data(
        pending_edit={"field": field, "value": new_value}
    )
    await state.set_state(EditMovie.confirm)

@router.callback_query(EditMovie.confirm, F.data == "confirm_edit:yes")
async def confirm_edit_yes(callback: CallbackQuery, state: FSMContext):
    """
    Сохраняем изменения и показываем обновлённую карточку фильма.
    """
    data = await state.get_data()
    pending = data.get("pending_edit")
    movie_id = data["movie_id"]
    user_id = callback.from_user.id

    if not pending:
        await callback.message.answer("❌ Ошибка: нет данных для сохранения.")
        await state.clear()
        return

    field = pending["field"]
    new_value = pending["value"]

    await update_movie(user_id, movie_id, **{field: new_value})

    # Получаем ОБНОВЛЁННЫЙ фильм
    movie = await get_movie_by_id(user_id, movie_id)
    if not movie:
        await clear_and_send(callback.message, "❌ Фильм не найден.", await get_main_menu_with_stats(user_id))
        await state.clear()
        return

    # Импортируем функцию форматирования
    from movie_bot.utils.helpers import get_movie_card_text

    # Клавиатура с полями
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="edit_field:title")],
        [InlineKeyboardButton(text="🎭 Жанр", callback_data="edit_field:genre")],
        [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field:description")],
        [InlineKeyboardButton(text="🖼 Постер", callback_data="edit_field:poster")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="edit_done")],
    ])

    # Показываем, что изменилось
    field_names = {"title": "Название", "genre": "Жанр", "description": "Описание", "poster": "Постер"}
    change_text = f"✅ Поле «{field_names[field]}» успешно обновлено!\n\n"

    # Отправляем карточку фильма
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
    """
    Завершает редактирование и возвращается в главное меню.
    """
    user_id = callback.from_user.id
    await clear_and_send(
        callback.message,
        "📌 Редактирование завершено. Все изменения сохранены.",
        await get_main_menu_with_stats(user_id)
    )
    await state.clear()
    await callback.answer()

@router.callback_query(EditMovie.confirm, F.data == "confirm_edit:no")
async def confirm_edit_no(callback: CallbackQuery, state: FSMContext):
    """
    Отмена изменения — показываем актуальную карточку.
    """
    data = await state.get_data()
    movie_id = data["movie_id"]
    user_id = callback.from_user.id
    movie = await get_movie_by_id(user_id, movie_id)

    from movie_bot.utils.helpers import get_movie_card_text

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