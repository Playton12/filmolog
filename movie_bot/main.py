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
import os
import signal
import sys
from pathlib import Path

from aiogram import Dispatcher

from movie_bot.config import BOT_TOKEN, ensure_directories
from movie_bot.bot import create_bot
from movie_bot.database.db import init_db
from movie_bot.utils.logger import get_logger
from movie_bot.utils.healthcheck import run_health_server, stop_health_server
from movie_bot.commands import get_commands

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
                logger.info(f"Подключён роутер: {module_name}")
            else:
                logger.warning(f"Роутер не найден в модуле: {module_name}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке {module_name}: {e}")


async def main():
    """
    Основная асинхронная функция запуска бота.
    """
    logger.info("Запуск бота...")
    logger.info(f"Версия Python: {sys.version}")
    logger.info(f"Рабочая директория: {os.getcwd()}")

    # Создаём директории (вместо side effect при импорте config)
    ensure_directories()

    # Инициализация БД
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.critical(f"Не удалось инициализировать БД: {e}", exc_info=True)
        sys.exit(1)

    # Создаём бота (вместо глобального Bot() при импорте)
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN не задан. Завершаю работу.")
        sys.exit(1)
    bot = create_bot(BOT_TOKEN)

    # Создаём диспетчер
    dp = Dispatcher()

    # Подключаем роутеры
    load_routers(dp)
    logger.info("Все обработчики загружены")

    # Устанавливаем команды
    try:
        await bot.set_my_commands(get_commands())
        logger.info("Команды бота установлены")
    except Exception as e:
        logger.error(f"Не удалось установить команды: {e}")

    # Health-check сервер (для Render.com)
    if os.getenv("RENDER"):
        run_health_server()
        logger.info("Health-check сервер запущен")

    # Graceful shutdown через asyncio-совместимый механизм
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def request_stop():
        logger.info("Получен сигнал остановки. Завершаю бота...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except NotImplementedError:
            # Windows не поддерживает add_signal_handler для SIGTERM
            pass

    # Запуск поллинга
    logger.info("Бот успешно запущен и готов к работе!")
    try:
        task = asyncio.create_task(dp.start_polling(bot))
        # Ждём либо сигнал остановки, либо завершение поллинга
        stop_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait(
            [task, stop_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        # Отменяем оставшуюся задачу
        for t in pending:
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
    except Exception as e:
        logger.critical(f"Критическая ошибка при поллинге: {e}", exc_info=True)
    finally:
        stop_health_server()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную.")
    except Exception as e:
        logger.critical(f"Необработанная ошибка в __main__: {e}")
        sys.exit(1)
