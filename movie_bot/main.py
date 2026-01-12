import asyncio
import logging

from aiogram import Dispatcher

from movie_bot.bot import bot
from movie_bot.database.db import init_db
from movie_bot.utils.logger import setup_logger

# ✅ Правильные абсолютные импорты
from movie_bot.handlers.start import router as start_router
from movie_bot.handlers.recommend import router as recommend_router
from movie_bot.handlers.add_movie import router as add_movie_router
from movie_bot.handlers.my_movies import router as my_movies_router
from movie_bot.handlers.watched import router as watched_router
from movie_bot.handlers.delete import router as delete_router


async def main():
    setup_logger()
    await init_db()

    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(recommend_router)
    dp.include_router(add_movie_router)
    dp.include_router(my_movies_router)
    dp.include_router(watched_router)
    dp.include_router(delete_router)

    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())