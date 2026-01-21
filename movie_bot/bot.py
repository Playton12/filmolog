"""
Глобальный экземпляр бота.
"""
from aiogram import Bot
from movie_bot.config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)