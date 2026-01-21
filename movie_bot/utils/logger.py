"""
Настройка логирования.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from movie_bot.config import LOGS_DIR


# Уровень логирования
LOG_LEVEL = logging.DEBUG if os.getenv("DEBUG") else logging.INFO


def setup_logger(name: str = "movie_bot", log_file: Path = None) -> logging.Logger:
    """
    Настраивает и возвращает отдельный логгер.

    :param name: Имя логгера (обычно __name__)
    :param log_file: Путь к файлу лога. Если None — используется LOGS_DIR / "bot.log"
    :return: Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    # Избегаем дублирования хэндлеров
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)
    logger.propagate = False  # Не передавать родительским

    # Формат
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Убедимся, что папка существует
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Файл лога
    log_file = log_file or (LOGS_DIR / "bot.log")
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8"  # ✅ Поддержка кириллицы
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"❌ Не удалось создать файл лога {log_file}: {e}")

    # Консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает настроенный логгер по имени.
    Автоматически вызывает setup_logger при первом обращении.
    """
    return setup_logger(name)