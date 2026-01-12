"""
Настройка системы логирования.

Функции:
- setup_logger — настраивает логирование в файл и консоль
"""

import logging

def setup_logger():
    """
    Настраивает логирование:
    - Уровень: INFO
    - Формат: время, имя, уровень, сообщение
    - Вывод: в файл `bot.log` и в консоль

    Вызывается один раз при старте бота.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )