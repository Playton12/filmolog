"""
Централизованный генератор текстов для бота.
Повышает переиспользуемость и упрощает локализацию в будущем.
"""

from datetime import datetime
from typing import Optional
from movie_bot.utils.text_utils import pluralize


class TextBuilder:
    # 🎬 Заголовки списков
    @staticmethod
    def list_header(title: str, total: int, page: int = None, total_pages: int = None) -> str:
        """
        Формирует заголовок списка с количеством и пагинацией.
        Пример: "✅ Просмотренные (12) | Страница 1/3"
        """
        page_info = f" | Страница {page + 1}/{total_pages}" if total_pages and total_pages > 1 else ""
        return f"{title} ({total}){page_info}:"

    # 🔍 Результаты поиска
    @staticmethod
    def search_results_text(total: int, query: str, page: int = None, total_pages: int = None) -> str:
        """
        Формирует текст для результата поиска.
        """
        page_info = f" | Страница {page + 1}/{total_pages}" if total_pages and total_pages > 1 else ""
        return (
            f"🔍 Найдено <b>{total}</b> по запросу:\n"
            f"“<i>{query}</i>”{page_info}"
        )

    # 📅 Форматирование даты
    @staticmethod
    def format_date(iso_date: Optional[str]) -> str:
        """
        Форматирует ISO-строку в читаемый вид: 17.04.2025
        """
        if not iso_date:
            return "—"
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y")
        except Exception:
            return "ошибка"

    # 🎟 Карточка фильма
    @staticmethod
    def movie_card(movie: dict) -> str:
        """
        Возвращает красиво отформатированную карточку фильма.
        """
        lines = [
            f"🎬 <b>{movie['title']}</b>",
            ""
        ]

        # Жанр
        genre_emoji = {
            "Фильм": "🎬",
            "Сериал": "📺",
            "Аниме": "🌸",
            "Мультфильм": "🎨"
        }.get(movie['genre'], "📌")

        lines.append(f"{genre_emoji} <b>Жанр:</b> <i>{movie['genre']}</i>")
        lines.append("")

        # Описание
        description = movie["description"] or "ℹ️ Описание не добавлено."
        if len(description) > 200:
            description = description[:197] + "..."
        lines.append(f"📝 <b>Описание:</b>\n<i>{description}</i>")
        lines.append("")

        # Дата добавления
        added_at = movie.get("added_at")
        if added_at:
            formatted_date = TextBuilder.format_date(added_at)
            lines.append(f"➕ <b>Добавлен:</b> <i>{formatted_date}</i>")
        else:
            lines.append("➕ <b>Добавлен:</b> <i>неизвестно</i>")
        lines.append("")

        # Статус просмотра
        if movie["watched"]:
            watched_at = movie.get("watched_at")
            if watched_at:
                formatted_date = TextBuilder.format_date(watched_at)
                lines.append(f"✅ <b>Просмотрен:</b> <i>{formatted_date}</i>")
            else:
                lines.append("✅ <b>Просмотрен:</b> <i>дата не зафиксирована</i>")
        else:
            lines.append("🟡 <b>Статус:</b> <i>в планах</i>")

        return "\n".join(lines)

    # 📊 Статистика в меню
    @staticmethod
    def main_menu_stats(total: int, watched: int) -> str:
        unwatched = total - watched
        total_word = pluralize(total, ("фильм", "фильма", "фильмов"))
        watched_word = pluralize(watched, ("просмотрен", "просмотрено", "просмотрено"))
        unwatched_word = pluralize(unwatched, ("остался", "осталось", "осталось"))

        if total == 0:
            return "📭 Пока нет контента"

        progress = (watched / total) * 100 if total > 0 else 0
        bar = "🟩" * int(progress // 10) + "◽️" * (10 - int(progress // 10))

        return (
            f"📚 <b>{total}</b> {total_word} | ✅ <b>{watched}</b> {watched_word}\n"
            f"📊 Прогресс: {bar} {int(progress)}%"
        )

    # ℹ️ Помощь
    @staticmethod
    def help_text() -> str:
        """
        Полный текст справки.
        """
        return """
🤖 <b>Добро пожаловать в бот для управления фильмами!</b>

📌 Вы можете использовать команды:

🎬 /add — Добавить контент
🎯 /recommend — Получить рекомендацию  
📂 /my_movies — Мой контент  
🔄 /restart — Перезапустить   
ℹ️ /help — Показать это сообщение

💡 Нажмите на команду — она выполнится!

🛠 <b>Совет:</b> Используйте /restart, если бот не отвечает.

Приятного просмотра! 🍿
        """.strip()

    # ✅ Успешные действия
    @staticmethod
    def success_add() -> str:
        return "🎉 <b>Контент успешно добавлен!</b>"

    @staticmethod
    def success_toggle_watched(title: str, watched: bool) -> str:
        status = "просмотрен" if watched else "возвращён в список"
        return f"✅ <b>Фильм «{title}»</b> помечен как <i>{status}</i>."

    # 🎬 Иконки для жанров
    @staticmethod
    def genre_button_text(genre: str) -> str:
        """
        Возвращает текст кнопки жанра с иконкой.
        """
        icons = {
            "Фильм": "🎬",
            "Сериал": "📺",
            "Аниме": "🌸",
            "Мультфильм": "🎨"
        }
        icon = icons.get(genre, "🎞")
        return f"{icon} {genre}"

    # 📝 Тексты кнопок
    @staticmethod
    def btn_add() -> str:
        return "➕ Добавить"

    @staticmethod
    def btn_recommend() -> str:
        return "🎯 Рекомендации"

    @staticmethod
    def btn_my_movies() -> str:
        return "📂 Мой контент"

    @staticmethod
    def btn_help() -> str:
        return "ℹ️ Помощь"

    @staticmethod
    def btn_cancel() -> str:
        return "❌ Отмена"

    @staticmethod
    def btn_back() -> str:
        return "🔙 Назад"

    @staticmethod
    def btn_skip_poster() -> str:
        return "🖼 Пропустить"

    @staticmethod
    def btn_toggle_watched(watched: bool) -> str:
        return "✅ Пометить как просмотренный" if watched else "⭕ Пометить как непросмотренный"

    @staticmethod
    def btn_edit() -> str:
        return "✏️ Редактировать"

    @staticmethod
    def btn_delete() -> str:
        return "🗑 Удалить"

    @staticmethod
    def btn_search() -> str:
        return "🔍 Поиск"

    @staticmethod
    def btn_all_movies(total: int) -> str:
        return f"📋 Все ({total})"

    # 📝 Шаги добавления
    @staticmethod
    def add_movie_step_title() -> str:
        return "🎬 <b>Добавление контента</b>\n\n📌 Напишите название.\n\n🔖 <i>Шаг 1 из 4</i>"

    @staticmethod
    def add_movie_step_genre() -> str:
        return "🎭 <b>Выберите жанр</b>\n\n🔖 <i>Шаг 2 из 4</i>"

    @staticmethod
    def add_movie_step_description() -> str:
        return "📝 <b>Напишите описание</b>\n\n🔖 <i>Шаг 3 из 4</i>"

    @staticmethod
    def add_movie_step_poster() -> str:
        return "🖼 <b>Пришлите постер</b> или нажмите «Пропустить»\n\n🔖 <i>Шаг 4 из 4</i>"

    # 🧠 Подсказки
    @staticmethod
    def suggest_correction(input: str, match: str) -> str:
        return f"🔍 Возможно, вы имели в виду: <b>{match}</b>?\n\nВы написали: <i>{input}</i>\n\nИсправить?"

    @staticmethod
    def confirm_duplicate(title: str) -> str:
        return f"⚠️ Контент <i>«{title}»</i> уже есть в библиотеке.\n\nДобавить повторно?"

    @staticmethod
    def err_title_empty() -> str:
        return "❌ Название не может быть пустым."

    @staticmethod
    def err_description_empty() -> str:
        return "❌ Описание не может быть пустым."

    @staticmethod
    def err_already_at_start() -> str:
        return "❌ Вы уже в начале."

    # ❌ Подтверждения
    @staticmethod
    def confirm_delete(title: str) -> str:
        return f"⚠️ Вы уверены, что хотите удалить контент:\n\n<b>{title}</b>?"

    @staticmethod
    def success_deleted(title: str) -> str:
        return f"🗑 Контент <b>{title}</b> успешно удалён."

    # 🔧 Редактирование
    @staticmethod
    def edit_enter_new_value(field_name: str) -> str:
        return f"✏️ Введите новое {field_name}:"

    @staticmethod
    def confirm_edit_field(field_name: str, icon: str, old_value: str, new_value: str) -> str:
        return (
            f"{icon} *Подтвердите изменение*\n\n"
            f"🗂 Поле: *{field_name}*\n"
            f"🔄 Старое: `{old_value}`\n"
            f"✅ Новое: `{new_value}`\n\n"
            f"Сохранить изменения?"
        )

    @staticmethod
    def success_edit_field(field_name: str, old_value: str, new_value: str) -> str:
        return (
            f"✅ *Поле обновлено*\n\n"
            f"🗂 {field_name}:\n"
            f"➡️ `{old_value}` → `{new_value}`\n\n"
        )

    # 📂 Мои фильмы
    @staticmethod
    def no_movies_yet() -> str:
        return "📭 У вас пока нет добавленного контента.\n\nДобавьте первый — нажмите «➕ Добавить»"

    @staticmethod
    def my_movies_intro(total: int, watched: int) -> str:
        return f"📂 У вас {total} контент{'а' if total % 10 in [2, 3, 4] and total // 10 != 1 else 'ов'}.\nВыберите действие:"

    @staticmethod
    def no_watched_movies() -> str:
        return "⭕ Нет просмотренного контента."

    @staticmethod
    def no_unwatched_movies() -> str:
        return "📭 Нет непросмотренного контента."

    @staticmethod
    def prompt_search() -> str:
        return "🔍 Введите название или жанр для поиска:"

    @staticmethod
    def err_search_empty() -> str:
        return "❌ Введите текст для поиска."

    @staticmethod
    def search_no_results(query: str) -> str:
        return f"❌ Ничего не найдено по запросу *{query}*.\n\nПопробуйте другое слово."

    @staticmethod
    def loading() -> str:
        return "Загрузка..."

    # 🎯 Рекомендации
    @staticmethod
    def recommend_choose_genre() -> str:
        return "🎬 Выберите жанр для рекомендации:"

    @staticmethod
    def recommend_no_movies_in_genre(genre: str) -> str:
        return f"🤷‍♂️ В жанре <b>{genre}</b> пока нет непросмотренного контента."

    @staticmethod
    def recommend_movie_caption(movie) -> str:
        title = movie['title']
        genre = movie['genre']
        description = movie['description'] or "Без описания"
        return (
            f"<b>🎬 Советую посмотреть: {title}</b>\n"
            f"<i>Жанр: {genre}</i>\n\n"
            f"{description}"
        )

    # 🔄 Перезапуск
    @staticmethod
    def restart_successful() -> str:
        return "🔄 Бот перезапущен.\n\n"

    @staticmethod
    def restart_failed() -> str:
        return "❌ Не удалось перезапустить сессию. Попробуйте /start."

    # 🏠 Главное меню
    @staticmethod
    def start_greeting() -> str:
        return "👋 Добро пожаловать! Добавляйте и управляйте своим контентом.\n\n"

    @staticmethod
    def main_menu_title() -> str:
        return "🏠 Главное меню\n\n"

    @staticmethod
    def start_failed() -> str:
        return "❌ Не удалось загрузить главное меню. Попробуйте /restart."

    @staticmethod
    def menu_failed() -> str:
        return "❌ Не удалось обновить меню. Попробуйте /restart."
    
    @staticmethod
    def get_movie_card_text(movie) -> str:
        return TextBuilder.movie_card(movie)