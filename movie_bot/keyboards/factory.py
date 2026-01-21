"""
Фабрика клавиатур — централизованное создание всех клавиатур бота.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from movie_bot.keyboards.genre import GENRES
from movie_bot.utils.text_builder import TextBuilder


class KeyboardFactory:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """
        Главное меню.
        """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_add(), callback_data="add")],
            [InlineKeyboardButton(text=TextBuilder.btn_recommend(), callback_data="recommend")],
            [InlineKeyboardButton(text=TextBuilder.btn_my_movies(), callback_data="my_movies")],
            [InlineKeyboardButton(text=TextBuilder.btn_help(), callback_data="help")]
        ])

    @staticmethod
    def cancel() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_cancel(), callback_data="back_main")]
        ])

    @staticmethod
    def back() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_step")],
            [InlineKeyboardButton(text=TextBuilder.btn_cancel(), callback_data="back_main")]
        ])

    @staticmethod
    def back_edit() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_to_edit")]
        ])

    @staticmethod
    def skip_poster() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_skip_poster(), callback_data="skip_poster")],
            [InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_step")],
            [InlineKeyboardButton(text=TextBuilder.btn_cancel(), callback_data="back_main")]
        ])

    @staticmethod
    def skip_poster_edit() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_skip_poster(), callback_data="skip_poster")],
            [InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_to_edit")]
        ])

    @staticmethod
    def genre(mode: str = "add") -> InlineKeyboardMarkup:
        """
        Клавиатура с жанрами.
        """
        config = {
            "add": {"prefix": "add_genre", "cancel_text": TextBuilder.btn_cancel(), "cancel_cb": "back_main"},
            "rec": {"prefix": "rec_genre", "cancel_text": TextBuilder.btn_back(), "cancel_cb": "back_main"},
            "edit": {"prefix": "edit_genre", "cancel_text": TextBuilder.btn_back(), "cancel_cb": "back_to_edit"}
        }.get(mode, {})

        keyboard = []
        for genre in GENRES:
            text = TextBuilder.genre_button_text(genre)
            callback_data = f"{config['prefix']}:{genre}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

        keyboard.append([
            InlineKeyboardButton(text=config["cancel_text"], callback_data=config["cancel_cb"])
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def movies(movies: list, action: str = "delete") -> InlineKeyboardMarkup:
        """
        Список фильмов.
        """
        buttons = []
        for movie in movies:
            buttons.append([
                InlineKeyboardButton(
                    text=f"🎬 {movie['title']}",
                    callback_data=f"{action}:{movie['id']}"
                )
            ])
        buttons.append([
            InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_main")
        ])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def confirmation(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
        """
        Универсальная клавиатура подтверждения.
        Текст передаётся не здесь, а в сообщении.
        """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data=yes_callback)],
            [InlineKeyboardButton(text="❌ Нет", callback_data=no_callback)],
            [InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_main")]
        ])

    @staticmethod
    def movie_actions(source: str = "my_movies", watched: bool = False, movie_id: int = None) -> InlineKeyboardMarkup:
        if not movie_id:
            raise ValueError("movie_id обязателен для movie_actions")

        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=TextBuilder.btn_toggle_watched(watched),
                callback_data=f"toggle_watched:{movie_id}:{source}"
            )],
            [InlineKeyboardButton(
                text=TextBuilder.btn_edit(),
                callback_data=f"edit_select:{movie_id}"
            )],
            [InlineKeyboardButton(
                text=TextBuilder.btn_delete(),
                callback_data=f"delete:{movie_id}:{source}"  # ✅ Передаём source
            )],
            [InlineKeyboardButton(
                text=TextBuilder.btn_back(),
                callback_data="back_main"
            )]
        ])

    @staticmethod
    def my_movies_menu(total: int) -> InlineKeyboardMarkup:
        """
        Меню "Мои фильмы".
        """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_all_movies(total), callback_data="my_movies_all")],
            [InlineKeyboardButton(text=TextBuilder.btn_search(), callback_data="my_movies_search")],
            [InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_main")]
        ])
    
    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """
        Кнопка «Назад в главное меню».
        """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TextBuilder.btn_back(), callback_data="back_main")]
        ])
    
    @staticmethod
    def movies_filter(watched_count: int, unwatched_count: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Просмотренные ({watched_count})", callback_data="my_movies_watched")],
            [InlineKeyboardButton(text=f"⭕ Непросмотренные ({unwatched_count})", callback_data="my_movies_unwatched")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_movies")]
        ])

    @staticmethod
    def after_empty(view: str) -> InlineKeyboardMarkup:
        back = "my_movies_all" if view in ["watched", "unwatched"] else "my_movies"
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Другая категория", callback_data=back)],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="my_movies")]
        ])

    @staticmethod
    def retry_search() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="my_movies_search")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="my_movies")]
        ])
    
    @staticmethod
    def edit_menu() -> InlineKeyboardMarkup:
        """
        Клавиатура выбора поля для редактирования.
        """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data="edit_field:title")],
            [InlineKeyboardButton(text="🎭 Жанр", callback_data="edit_field:genre")],
            [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field:description")],
            [InlineKeyboardButton(text="🖼 Постер", callback_data="edit_field:poster_id")],
            [InlineKeyboardButton(text="✅ Готово", callback_data="edit_done")],
        ])
    
    @staticmethod
    def confirm_delete_for_movie(movie_id: int, source: str) -> InlineKeyboardMarkup:
        """
        Клавиатура подтверждения удаления.
        Да → в список, Нет/Назад → в карточку фильма.
        """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Да, удалить",
                callback_data=f"confirm_delete:{movie_id}:{source}"
                )],
            [InlineKeyboardButton(
                text="❌ Нет",
                callback_data=f"movie_info:{movie_id}:{source}"
            )],
            [InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"movie_info:{movie_id}:{source}"
            )]
        ])