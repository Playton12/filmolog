import asyncio
import logging
import os
from threading import Thread

from aiogram import Dispatcher

from movie_bot.bot import bot
from movie_bot.database.db import init_db
from movie_bot.utils.logger import setup_logger
from movie_bot.utils.healthcheck import run_server

# Импорт роутеров
from movie_bot.handlers.start import router as start_router
from movie_bot.handlers.restart import router as restart_router
from movie_bot.handlers.recommend import router as recommend_router
from movie_bot.handlers.add_movie import router as add_movie_router
from movie_bot.handlers.my_movies import router as my_movies_router
from movie_bot.handlers.watched import router as watched_router
from movie_bot.handlers.delete import router as delete_router
from movie_bot.handlers.edit_movie import router as edit_movie_router
from movie_bot.handlers.help import router as help_router

# Импорт команд
from movie_bot.utils.commands import get_commands


async def main():
    setup_logger()
    await init_db()

    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(restart_router)
    dp.include_router(recommend_router)
    dp.include_router(edit_movie_router)
    dp.include_router(add_movie_router)
    dp.include_router(my_movies_router)
    dp.include_router(watched_router)
    dp.include_router(delete_router)
    dp.include_router(help_router)

    # Устанавливаем команды
    await bot.set_my_commands(get_commands())  # ✅ Чисто и понятно

    # Запускаем health-check сервер в отдельном потоке
    if os.getenv("RENDER"):
        thread = Thread(target=run_server, daemon=True)
        thread.start()

    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())