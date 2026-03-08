from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import main_keyboard
from app.config.servers import SERVERS

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name if message.from_user else "странник"
    text = (
        f"👋 Привет, <b>{name}</b>! Я бот для управления серверами Minecraft 😁\n\n"
        "🎮 Выбери сервер из меню ниже, чтобы посмотреть статус или управлять им.\n\n"
        "❓ /help — список команд"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard())


@router.message(Command("servers"))
async def cmd_servers(message: Message) -> None:
    if not SERVERS:
        await message.answer("😶 Серверов не настроено.")
        return
    await message.answer("🎮 Выбери сервер по которому хочешь посмотреть информацию:", reply_markup=main_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "📖 <b>Справка по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — Приветствие\n"
        "/servers — Список серверов\n"
        "/help — Эта справка\n\n"
        "<b>Как пользоваться:</b>\n"
        "Нажми кнопку с именем сервера — откроется карточка.\n"
        "Там доступны:\n"
        "  • 🔄 <b>Обновить</b> — обновить статус\n"
        "  • ▶️ <b>Запустить</b> — запустить сервер (доступно всем)\n"
        "  • ⛔ <b>Остановить</b> — выключить сервер если он пустой\n"
        "  • 💬 <b>RCON</b> — отправить команду прямо на сервер (только админ)\n\n"
        "💡 После запуска сервера придёт уведомление когда он будет готов!"
    )
    await message.answer(text, parse_mode="HTML")
