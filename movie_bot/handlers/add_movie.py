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
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from movie_bot.fsm.states import AddMovie
from movie_bot.keyboards.genre import get_genre_keyboard
from movie_bot.keyboards.utils import get_cancel_button, get_back_button, get_skip_poster_button
from movie_bot.database.queries import add_movie, is_movie_exists, get_all_movies
from movie_bot.utils.helpers import get_similar_movies, clear_and_send
from movie_bot.keyboards.main_menu import get_main_menu_with_stats

router = Router()

@router.callback_query(F.data == "add")
async def add_movie_start(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс добавления фильма.

    Устанавливает состояние `AddMovie.title` и запрашивает название.

    :param callback: Callback-запрос от кнопки "Добавить"
    :param state: Контекст FSM
    """
    await state.set_state(AddMovie.title)
    await state.update_data(step=1)
    text = "📝 Напишите название фильма\n\n🔖 Шаг 1 из 4"
    await clear_and_send(callback.message, text, get_cancel_button())
    await callback.answer()

@router.message(AddMovie.title)
async def add_title(message: Message, state: FSMContext):
    """
    Обрабатывает ввод названия фильма.

    Проверяет:
    - На наличие похожих названий (через fuzzy-поиск)
    - На точные дубликаты

    :param message: Сообщение с названием
    :param state: Контекст FSM
    """
    if not message.text or not message.text.strip():
        await message.answer("❌ Название не может быть пустым.", reply_markup=get_cancel_button())
        return

    user_input = message.text.strip()
    user_id = message.from_user.id

    user_movies = await get_all_movies(user_id=user_id, watched=False)

    # Проверка похожих названий
    similar_list = get_similar_movies(user_movies, user_input, threshold=75)
    best_match = similar_list[0]["movie"]["title"] if similar_list else None

    if best_match:
        await state.update_data(title=user_input)
        await message.answer(
            f"🔍 Возможно, вы имели в виду: *{best_match}*?\n\nВы написали: *{user_input}*\n\nИсправить?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data=f"auto_correct:{best_match}")],
                [InlineKeyboardButton(text="❌ Нет", callback_data="auto_skip_correction")],
            ]),
            parse_mode="Markdown"
        )
        return

    # Проверка точного совпадения
    if await is_movie_exists(user_id, user_input):
        similar_movies = get_similar_movies(user_movies, user_input, threshold=70)
        similar_text = "\n".join([f"• {m['title']} ({m['genre']})" for m in similar_movies])
        await state.update_data(title=user_input)
        await message.answer(
            f"⚠️ Фильм с названием *{user_input}* уже есть.{similar_text}\n\nДобавить повторно?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data="confirm_duplicate_yes")],
                [InlineKeyboardButton(text="❌ Нет", callback_data="confirm_duplicate_no")]
            ]),
            parse_mode="Markdown"
        )
        return

    await state.update_data(title=user_input, step=2)
    await state.set_state(AddMovie.genre)
    await message.answer("🎭 Выберите жанр\n\n🔖 Шаг 2 из 4", reply_markup=get_genre_keyboard("add"))

# --- Автоисправление ---
@router.callback_query(F.data.startswith("auto_correct:"))
async def auto_correct_title(callback: CallbackQuery, state: FSMContext):
    """
    Автоматически исправляет название на похожее.

    :param callback: Callback с предложенным названием
    :param state: Контекст FSM
    """
    corrected_title = callback.data.split(":", 1)[1]
    await state.update_data(title=corrected_title, step=2)
    await state.set_state(AddMovie.genre)
    await clear_and_send(callback.message, "🎭 Выберите жанр\n\n🔖 Шаг 2 из 4", get_genre_keyboard("add"))
    await callback.answer()

@router.callback_query(F.data == "auto_skip_correction")
async def auto_skip_correction(callback: CallbackQuery, state: FSMContext):
    """
    Пропускает автоисправление и продолжает с оригинальным названием.

    :param callback: Callback от кнопки "Нет"
    :param state: Контекст FSM
    """
    data = await state.get_data()
    await state.update_data(step=2)
    await state.set_state(AddMovie.genre)
    await clear_and_send(callback.message, "🎭 Выберите жанр\n\n🔖 Шаг 2 из 4", get_genre_keyboard("add"))
    await callback.answer()

# --- Жанр ---
@router.callback_query(AddMovie.genre, F.data.startswith("add_genre:"))
async def add_genre_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор жанра.

    Переходит к вводу описания.

    :param callback: Callback с выбранным жанром
    :param state: Контекст FSM
    """
    await callback.answer()
    genre = callback.data.split(":", 1)[1]
    await state.update_data(genre=genre, step=3)
    await state.set_state(AddMovie.description)
    await clear_and_send(callback.message, "📝 Напишите описание\n\n🔖 Шаг 3 из 4", get_back_button())

# --- Описание ---
@router.message(AddMovie.description)
async def add_description(message: Message, state: FSMContext):
    """
    Обрабатывает ввод описания фильма.

    Переходит к шагу с постером.

    :param message: Сообщение с описанием
    :param state: Контекст FSM
    """
    if not message.text or not message.text.strip():
        await message.answer("❌ Описание не может быть пустым.", reply_markup=get_back_button())
        return
    await state.update_data(description=message.text.strip(), step=4)
    await state.set_state(AddMovie.poster)
    await message.answer("🖼 Пришлите фото постера или пропустите\n\n🔖 Шаг 4 из 4", reply_markup=get_skip_poster_button())

# --- Постер ---
@router.message(AddMovie.poster, F.photo)
async def add_poster_photo(message: Message, state: FSMContext):
    """
    Обрабатывает отправку постера.

    Сохраняет фильм в БД и завершает процесс.

    :param message: Сообщение с фото
    :param state: Контекст FSM
    """
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
    await message.answer("✅ Фильм успешно добавлен!", reply_markup=keyboard)

@router.callback_query(AddMovie.poster, F.data == "skip_poster")
async def skip_poster(callback: CallbackQuery, state: FSMContext):
    """
    Пропускает шаг с постером.

    Сохраняет фильм без изображения.

    :param callback: Callback от кнопки "Пропустить"
    :param state: Контекст FSM
    """
    data = await state.get_data()
    await add_movie(
        user_id=callback.from_user.id,
        title=data["title"],
        genre=data["genre"],
        description=data["description"]
    )
    await state.clear()
    await clear_and_send(callback.message, "✅ Фильм успешно добавлен!", await get_main_menu_with_stats(callback.from_user.id))
    await callback.answer()