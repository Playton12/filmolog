"""
Точка входа в бота.

Задачи:
- Настройка логирования
- Инициализация базы данных
- Регистрация обработчиков (авто-загрузка)
- Установка команд
- Запуск поллинга
- Поддержка Render.com (health-check)
- Graceful shutdown
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from threading import Thread
from aiogram import Dispatcher

from movie_bot.bot import bot
from movie_bot.database.db import init_db
from movie_bot.utils.logger import get_logger
from movie_bot.utils.healthcheck import run_health_server, stop_health_server
from movie_bot.commands import get_commands

# --- Настройка логгера ---
logger = get_logger(__name__)


def load_routers(dp: Dispatcher):
    """
    Автоматически импортирует и подключает все роутеры из movie_bot.handlers.
    Ожидается, что каждый файл содержит переменную `router`.
    """
    handlers_dir = Path(__file__).parent / "handlers"
    for file in handlers_dir.glob("*.py"):
        if file.name.startswith("__"):
            continue

        module_name = file.stem
        try:
            module = __import__(f"movie_bot.handlers.{module_name}", fromlist=["router"])
            if hasattr(module, "router"):
                dp.include_router(module.router)
                logger.info(f"✅ Подключён роутер: {module_name}")
            else:
                logger.warning(f"⚠️ Роутер не найден в модуле: {module_name}")
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке {module_name}: {e}")


async def main():
    """
    Основная асинхронная функция запуска бота.
    """
    logger.info("🚀 Запуск бота...")
    logger.info(f"📍 Версия Python: {sys.version}")
    logger.info(f"📍 Рабочая директория: {os.getcwd()}")

    # Инициализация БД
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.critical(f"❌ Не удалось инициализировать БД: {e}", exc_info=True)
        sys.exit(1)

    # Создаём диспетчер
    dp = Dispatcher()

    # Подключаем роутеры
    load_routers(dp)
    logger.info("✅ Все обработчики загружены")

    # Устанавливаем команды
    try:
        await bot.set_my_commands(get_commands())
        logger.info("✅ Команды бота установлены")
    except Exception as e:
        logger.error(f"❌ Не удалось установить команды: {e}")

    # Health-check сервер (для Render.com)
    if os.getenv("RENDER"):
        run_health_server()
        logger.info("🌐 Health-check сервер запущен (порт из переменной PORT)")

    # Graceful shutdown
    def stop_bot(*args):
        logger.info("🛑 Получен сигнал остановки. Завершаю бота...")
        stop_health_server()
        asyncio.create_task(dp.stop_polling())
        sys.exit(0)

    signal.signal(signal.SIGINT, stop_bot)
    signal.signal(signal.SIGTERM, stop_bot)

    # Запуск поллинга
    logger.info("🎬 Бот успешно запущен и готов к работе! 🚀")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при поллинге: {e}", exc_info=True)
    finally:
        stop_health_server()
        logger.info("🔚 Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен вручную.")
    except Exception as e:
        logger.critical(f"💥 Необработанная ошибка в __main__: {e}")
        sys.exit(1)