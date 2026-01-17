"""
Обработчик команды /help.
Показывает описание всех функций бота с кнопкой возврата.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from movie_bot.keyboards.main_menu import get_main_menu_with_stats

router = Router()

HELP_TEXT = """
🤖 <b>Добро пожаловать в бот для управления фильмами!</b>

📌 Вот что я умею:

🎬 <code>/add</code> — <b>Добавить фильм</b>
   Укажите название, жанр, описание и пришлите постер

🎯 <code>/recommend</code> — <b>Рекомендация</b>
   Получите случайный непросмотренный фильм

📂 <code>/my_movies</code> — <b>Мои фильмы</b>
   Просмотр всех, поиск, фильтры: просмотренные / непросмотренные

🔄 <code>/restart</code> — <b>Перезапустить бот</b>
   Сброс состояния, если что-то пошло не так

🛠 <i>Совет: используйте /restart, если бот не отвечает или завис</i>

💬 Бот помогает вести учёт фильмов и не забыть ни одного просмотра.
Приятного использования! 🍿
"""

# Клавиатура с кнопкой возврата
back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="back_main")]
])


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Отправляет справку с кнопкой возврата.
    """
    await message.answer(HELP_TEXT, reply_markup=back_keyboard, parse_mode="HTML")


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """
    Обработчик кнопки "Помощь" — показывает справку с кнопкой.
    """
    await callback.message.edit_text(HELP_TEXT, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()