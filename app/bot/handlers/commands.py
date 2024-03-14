from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import main_keyboard
from app.config.servers import SERVERS

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Я управляю серверами Minecraft.\n\n"
        "Выбери сервер из меню ниже, чтобы посмотреть статус или управлять им.\n\n"
        "/help — список команд"
    )
    await message.answer(text, reply_markup=main_keyboard())


@router.message(Command("servers"))
async def cmd_servers(message: Message) -> None:
    if not SERVERS:
        await message.answer("Серверов не настроено.")
        return
    await message.answer("Выбери сервер:", reply_markup=main_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "<b>Команды:</b>\n\n"
        "/start — Приветствие\n"
        "/servers — Список серверов\n"
        "/help — Справка\n\n"
        "<b>Как пользоваться:</b>\n"
        "Нажми кнопку с именем сервера — откроется карточка.\n"
        "Там доступны:\n"
        "  • <b>Обновить</b> — обновить статус\n"
        "  • <b>Запустить / Остановить</b> — управление контейнером\n"
        "  • <b>RCON</b> — отправить команду прямо на сервер\n"
    )
    await message.answer(text, parse_mode="HTML")
