from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import commands, server
from app.config.settings import settings


def create_bot() -> Bot:
    return Bot(token=settings.telegram_bot_token)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(commands.router)
    dp.include_router(server.router)
    return dp
