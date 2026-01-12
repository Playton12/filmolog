"""
Экземпляр Telegram-бота.

Содержит:
- Токен из .env
- Глобальный экземпляр `Bot`
"""

from aiogram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env")

bot = Bot(token=TOKEN)