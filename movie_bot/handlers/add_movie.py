"""
Обработчики добавления нового фильма.

Пошаговый сценарий:
1. Ввод названия
2. Выбор жанра
3. Ввод описания
4. Отправка постера (или пропуск)

Включает:
- Автоисправление названий (fuzzy-поиск)
- Проверку дубликатов
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from movie_bot.fsm.states import AddMovie
from movie_bot.keyboards.genre import get_genre_keyboard
from movie_bot.keyboards.utils import get_cancel_button, get_back_button, get_skip_poster_button, get_genre_with_navigation
from movie_bot.database.queries import add_movie, is_movie_exists, get_all_movies
from movie_bot.utils.helpers import get_similar_movies, clear_and_send
from movie_bot.keyboards.main_menu import get_main_menu_with_stats

router = Router()


@router.callback_query(F.data == "add")
async def add_movie_start(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс добавления фильма.
    """
    await state.set_state(AddMovie.title)
    await state.update_data(step=1)
    text = (
        "🎬 <b>Добавление фильма</b>\n\n"
        "📌 Напишите название фильма.\n\n"
        "🔖 <i>Шаг 1 из 4</i>"
    )
    await clear_and_send(callback.message, text, get_cancel_button(), parse_mode="HTML")
    await callback.answer()


@router.message(AddMovie.title)
async def add_title(message: Message, state: FSMContext):
    """
    Обрабатывает ввод названия фильма.
    """
    if not message.text or not message.text.strip():
        await message.answer("❌ Название не может быть пустым.", reply_markup=get_cancel_button())
        return

    user_input = message.text.strip()
    user_id = message.from_user.id
    user_movies = await get_all_movies(user_id=user_id, watched=None)

    # Проверка похожих названий
    similar_list = get_similar_movies(user_movies, user_input, threshold=75)
    best_match = similar_list[0] if similar_list else None

    if best_match:
        await state.update_data(title=user_input)
        await message.answer(
            f"🔍 Возможно, вы имели в виду: <b>{best_match}</b>?\n\n"
            f"Вы написали: <i>{user_input}</i>\n\n"
            "Исправить?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data=f"auto_correct:{best_match}")],
                [InlineKeyboardButton(text="❌ Нет", callback_data="auto_skip_correction")],
            ]),
            parse_mode="HTML"
        )
        return

    # Проверка точного совпадения
    if await is_movie_exists(user_id, user_input):
        await state.update_data(title=user_input)
        await message.answer(
            f"⚠️ Фильм <i>«{user_input}»</i> уже есть в вашей библиотеке.\n\n"
            "Добавить повторно?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data="confirm_duplicate_yes")],
                [InlineKeyboardButton(text="❌ Нет", callback_data="confirm_duplicate_no")]
            ]),
            parse_mode="HTML"
        )
        return

    await state.update_data(title=user_input, step=2)
    await state.set_state(AddMovie.genre)
    await message.answer(
        "🎭 <b>Выберите жанр</b>\n\n"
        "🔖 <i>Шаг 2 из 4</i>",
        reply_markup=get_genre_with_navigation()
    )


@router.callback_query(F.data.startswith("auto_correct:"))
async def auto_correct_title(callback: CallbackQuery, state: FSMContext):
    corrected_title = callback.data.split(":", 1)[1]
    await state.update_data(title=corrected_title, step=2)
    await state.set_state(AddMovie.genre)
    await clear_and_send(
        callback.message,
        "🎭 <b>Выберите жанр</b>\n\n🔖 <i>Шаг 2 из 4</i>",
        get_genre_with_navigation(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "auto_skip_correction")
async def auto_skip_correction(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(step=2)
    await state.set_state(AddMovie.genre)
    await clear_and_send(
        callback.message,
        "🎭 <b>Выберите жанр</b>\n\n🔖 <i>Шаг 2 из 4</i>",
        get_genre_with_navigation(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(AddMovie.genre, F.data.startswith("add_genre:"))
async def add_genre_callback(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split(":", 1)[1]
    await state.update_data(genre=genre, step=3)
    await state.set_state(AddMovie.description)
    await clear_and_send(
        callback.message,
        "📝 <b>Напишите описание</b>\n\n🔖 <i>Шаг 3 из 4</i>",
        get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_step")
async def back_to_previous_field(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()

    if current_state == AddMovie.description:
        await state.set_state(AddMovie.genre)
        await clear_and_send(
            callback.message,
            "🎭 <b>Выберите жанр</b>\n\n🔖 <i>Шаг 2 из 4</i>",
            get_genre_with_navigation(),
            parse_mode="HTML"
        )
    elif current_state == AddMovie.genre:
        await state.set_state(AddMovie.title)
        await clear_and_send(
            callback.message,
            "🎬 <b>Введите название фильма</b>\n\n🔖 <i>Шаг 1 из 4</i>",
            get_cancel_button(),
            parse_mode="HTML"
        )
    elif current_state == AddMovie.poster:
        await state.set_state(AddMovie.description)
        await clear_and_send(
            callback.message,
            "📝 <b>Напишите описание</b>\n\n🔖 <i>Шаг 3 из 4</i>",
            get_back_button(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Вы уже в начале.")

    await callback.answer()


@router.message(AddMovie.description)
async def add_description(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("❌ Описание не может быть пустым.", reply_markup=get_back_button())
        return
    await state.update_data(description=message.text.strip(), step=4)
    await state.set_state(AddMovie.poster)
    await message.answer(
        "🖼 <b>Пришлите постер</b> или нажмите «Пропустить»\n\n🔖 <i>Шаг 4 из 4</i>",
        reply_markup=get_skip_poster_button()
    )


@router.message(AddMovie.poster, F.photo)
async def add_poster_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_movie(
        user_id=message.from_user.id,
        title=data["title"],
        genre=data["genre"],
        description=data["description"],
        poster_id=message.photo[-1].file_id
    )
    await state.clear()
    keyboard = await get_main_menu_with_stats(message.from_user.id)
    await message.answer("🎉 <b>Фильм успешно добавлен!</b>", reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(AddMovie.poster, F.data == "skip_poster")
async def skip_poster(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await add_movie(
        user_id=callback.from_user.id,
        title=data["title"],
        genre=data["genre"],
        description=data["description"]
    )
    await state.clear()
    await clear_and_send(
        callback.message,
        "🎉 <b>Фильм успешно добавлен!</b>",
        await get_main_menu_with_stats(callback.from_user.id),
        parse_mode="HTML"
    )
    await callback.answer()