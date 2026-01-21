"""
Обработчики добавления фильма — с использованием MovieService, TextBuilder и KeyboardFactory.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from movie_bot.fsm import AddMovie
from movie_bot.services.movie_service import MovieService
from movie_bot.keyboards.factory import KeyboardFactory
from movie_bot.keyboards.main_menu import get_main_menu_with_stats
from movie_bot.utils.helpers import clear_and_send
from movie_bot.utils.text_builder import TextBuilder

router = Router()
logger = logging.getLogger(__name__)


# === Начало ===
@router.message(Command("add"))
@router.callback_query(F.data == "add")
async def cmd_add(event, state: FSMContext):
    """
    Начинает сценарий добавления фильма.
    """
    await state.set_state(AddMovie.title)
    await clear_and_send(
        event,
        TextBuilder.add_movie_step_title(),
        KeyboardFactory.cancel(),
        parse_mode="HTML"
    )


# === Ввод названия ===
@router.message(AddMovie.title)
async def add_title(message: Message, state: FSMContext):
    """
    Обрабатывает ввод названия.
    Проверяет на пустоту, похожие и дубликаты.
    """
    if not message.text or not message.text.strip():
        await message.answer(TextBuilder.err_title_empty(), reply_markup=KeyboardFactory.cancel())
        return

    user_input = message.text.strip()
    user_id = message.from_user.id

    # Поиск похожих
    similar = await MovieService.find_similar(user_id, user_input)
    if similar:
        match = similar[0]
        kb = KeyboardFactory.confirmation(
            yes_callback=f"auto_correct:{match}",
            no_callback="auto_skip_correction"
        )
        await message.answer(
            TextBuilder.suggest_correction(input=user_input, match=match),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await state.update_data(title=user_input)
        return

    # Проверка дубликата
    if await MovieService.exists(user_id, user_input):
        kb = KeyboardFactory.confirmation(
            yes_callback="confirm_duplicate_yes",
            no_callback="confirm_duplicate_no"
        )
        await message.answer(
            TextBuilder.confirm_duplicate(title=user_input),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await state.update_data(title=user_input)
        return

    # Сохраняем и переходим к жанру
    await state.update_data(title=user_input)
    await goto_genre_step(message, state)


# === Переход к жанру ===
async def goto_genre_step(event, state: FSMContext):
    """
    Отправляет шаг выбора жанра.
    Поддерживает Message и CallbackQuery.
    """
    await state.set_state(AddMovie.genre)
    await clear_and_send(
        event,
        TextBuilder.add_movie_step_genre(),
        KeyboardFactory.genre("add"),
        parse_mode="HTML"
    )


# === Выбор жанра ===
@router.callback_query(AddMovie.genre, F.data.startswith("add_genre:"))
async def add_genre_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор жанра.
    """
    try:
        genre = callback.data.split(":", 1)[1]
        await state.update_data(genre=genre)
        await state.set_state(AddMovie.description)
        await clear_and_send(
            callback.message,
            TextBuilder.add_movie_step_description(),
            KeyboardFactory.back(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"[add_movie] Ошибка при выборе жанра: {e}")
        await callback.answer("❌ Ошибка при выборе жанра.", show_alert=True)


# === Назад ===
@router.callback_query(F.data == "back_step")
async def back_to_previous_field(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает к предыдущему шагу.
    """
    current_state = await state.get_state()

    if current_state == AddMovie.description:
        await goto_genre_step(callback, state)
    elif current_state == AddMovie.genre:
        await state.set_state(AddMovie.title)
        await clear_and_send(
            callback.message,
            TextBuilder.add_movie_step_title(),
            KeyboardFactory.cancel(),
            parse_mode="HTML"
        )
    elif current_state == AddMovie.poster:
        await state.set_state(AddMovie.description)
        await clear_and_send(
            callback.message,
            TextBuilder.add_movie_step_description(),
            KeyboardFactory.back(),
            parse_mode="HTML"
        )
    else:
        await callback.answer(TextBuilder.err_already_at_start(), show_alert=True)

    await callback.answer()


# === Описание ===
@router.message(AddMovie.description)
async def add_description(message: Message, state: FSMContext):
    """
    Обрабатывает ввод описания.
    """
    if not message.text or not message.text.strip():
        await message.answer(TextBuilder.err_description_empty(), reply_markup=KeyboardFactory.back())
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(AddMovie.poster)
    await message.answer(
    TextBuilder.add_movie_step_poster(),
    reply_markup=KeyboardFactory.skip_poster(),
    parse_mode="HTML"
)


# === Постер или пропуск ===
@router.message(AddMovie.poster, F.photo)
async def add_poster_photo(message: Message, state: FSMContext):
    """
    Обрабатывает загрузку постера.
    """
    data = await state.get_data()
    try:
        await MovieService.create(
            user_id=message.from_user.id,
            title=data["title"],
            genre=data["genre"],
            description=data["description"],
            poster_id=message.photo[-1].file_id
        )
        await finish_addition(message, message.from_user.id)
        await state.clear()
    except Exception as e:
        logger.error(f"[add_movie] Ошибка при добавлении с постером: {e}")
        await message.answer("❌ Ошибка при сохранении. Попробуйте снова.")
        await state.clear()


@router.callback_query(AddMovie.poster, F.data == "skip_poster")
async def skip_poster(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает пропуск постера.
    """
    data = await state.get_data()
    try:
        await MovieService.create(
            user_id=callback.from_user.id,
            title=data["title"],
            genre=data["genre"],
            description=data["description"]
        )
        await finish_addition(callback.message, callback.from_user.id)
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.error(f"[add_movie] Ошибка при добавлении без постера: {e}")
        await callback.message.answer("❌ Ошибка при сохранении.")
        await state.clear()
        await callback.answer()


# === Завершение ===
async def finish_addition(event, user_id: int):
    """
    Завершает процесс добавления: показывает успех и главное меню.
    """
    try:
        stats_text, keyboard = await get_main_menu_with_stats(user_id)
        await clear_and_send(
            event,
            TextBuilder.success_add(),
            keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"[add_movie] Ошибка при завершении добавления: {e}")
        # Fallback
        await clear_and_send(
            event,
            TextBuilder.success_add(),
            KeyboardFactory.main_menu(),
            parse_mode="HTML"
        )