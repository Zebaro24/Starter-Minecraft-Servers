import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import ServerCallback, cancel_keyboard, main_keyboard, server_card_keyboard
from app.config.servers import SERVERS, SERVERS_BY_ID, ServerConfig
from app.config.settings import settings
from app.servers.manager import DockerServerManager
from app.servers.models import ServerInfo, ServerStatus
from app.servers.rcon import RCONError

logger = logging.getLogger(__name__)

router = Router()
manager = DockerServerManager()


# ---------------------------------------------------------------------------
# FSM
# ---------------------------------------------------------------------------


class RconState(StatesGroup):
    waiting_command = State()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _status_line(status: ServerStatus) -> str:
    icons = {
        ServerStatus.RUNNING: "Online",
        ServerStatus.STOPPED: "Выключен",
        ServerStatus.STARTING: "Запускается...",
        ServerStatus.STOPPING: "Выключается...",
        ServerStatus.UNKNOWN: "Неизвестно",
    }
    badges = {
        ServerStatus.RUNNING: "",
        ServerStatus.STOPPED: "",
        ServerStatus.STARTING: "",
        ServerStatus.STOPPING: "",
        ServerStatus.UNKNOWN: "",
    }
    return f"{badges[status]} {icons[status]}"


def _format_card(config: ServerConfig, info: ServerInfo) -> str:
    lines = [
        f"<b>{html.escape(config.name)}</b>",
        "",
        f"<b>Статус:</b> {_status_line(info.status)}",
    ]

    if info.status == ServerStatus.RUNNING:
        lines.append(f"<b>Игроков:</b> {info.players_online} / {info.players_max}")
        if info.players:
            lines.append("")
            for i, player in enumerate(info.players, 1):
                lines.append(f"  {i}. {html.escape(player.name)}")
        else:
            lines.append("<i>Никого нет на сервере</i>")

    return "\n".join(lines)


async def _render_card(
    config: ServerConfig,
    bot: Bot,
    chat_id: int,
    message_id: int | None = None,
) -> None:
    info = await manager.get_server_info(config)
    text = _format_card(config, info)
    keyboard = server_card_keyboard(config, info.status)

    if message_id:
        try:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except TelegramBadRequest:
            pass
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=keyboard)


def _is_admin(user_id: int) -> bool:
    return user_id == settings.telegram_admin_id


# ---------------------------------------------------------------------------
# Reply keyboard: tap server name
# ---------------------------------------------------------------------------


@router.message(F.text.in_([s.name for s in SERVERS]))
async def on_server_name(message: Message, bot: Bot) -> None:
    config = next((s for s in SERVERS if s.name == message.text), None)
    if config:
        await _render_card(config, bot, message.chat.id)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@router.callback_query(ServerCallback.filter(F.action == "info"))
async def cb_info(callback: CallbackQuery, callback_data: ServerCallback, bot: Bot) -> None:
    config = SERVERS_BY_ID.get(callback_data.server_id)
    if not config:
        await callback.answer("Сервер не найден.", show_alert=True)
        return
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await _render_card(config, bot, callback.message.chat.id, callback.message.message_id)


@router.callback_query(ServerCallback.filter(F.action == "start"))
async def cb_start(callback: CallbackQuery, callback_data: ServerCallback, bot: Bot) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Только администратор может запускать серверы.", show_alert=True)
        return

    config = SERVERS_BY_ID.get(callback_data.server_id)
    if not config:
        await callback.answer("Сервер не найден.", show_alert=True)
        return

    if not isinstance(callback.message, Message):
        return
    await callback.answer("Запускаю...")
    success = manager.start(config)

    if success:
        await bot.edit_message_text(
            text=f"<b>{html.escape(config.name)}</b>\n\n "
            f"Запускается... это может занять несколько минут.\n\n"
            f"Нажми <b>Обновить</b> чтобы проверить статус.",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            parse_mode="HTML",
            reply_markup=server_card_keyboard(config, ServerStatus.STARTING),
        )
    else:
        await callback.answer("Не удалось запустить сервер. Проверь Docker.", show_alert=True)


@router.callback_query(ServerCallback.filter(F.action == "stop"))
async def cb_stop(callback: CallbackQuery, callback_data: ServerCallback, bot: Bot) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Только администратор может останавливать серверы.", show_alert=True)
        return

    config = SERVERS_BY_ID.get(callback_data.server_id)
    if not config:
        await callback.answer("Сервер не найден.", show_alert=True)
        return

    if not isinstance(callback.message, Message):
        return
    await callback.answer("Останавливаю...")
    success = manager.stop(config)

    if success:
        await bot.edit_message_text(
            text=f"<b>{html.escape(config.name)}</b>\n\n "
            f"Выключается... подожди немного.\n\n"
            f"Нажми <b>Обновить</b> чтобы проверить статус.",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            parse_mode="HTML",
            reply_markup=server_card_keyboard(config, ServerStatus.STOPPING),
        )
    else:
        await callback.answer("Не удалось остановить сервер. Проверь Docker.", show_alert=True)


@router.callback_query(ServerCallback.filter(F.action == "rcon"))
async def cb_rcon(callback: CallbackQuery, callback_data: ServerCallback, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Только администратор может отправлять RCON команды.", show_alert=True)
        return

    config = SERVERS_BY_ID.get(callback_data.server_id)
    if not config:
        await callback.answer("Сервер не найден.", show_alert=True)
        return

    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    await state.set_state(RconState.waiting_command)
    await state.update_data(server_id=config.id, card_message_id=callback.message.message_id)
    await callback.answer()

    await callback.message.answer(
        f"<b>RCON  {html.escape(config.name)}</b>\n\n"
        "Введи команду для отправки на сервер:\n"
        "<i>Примеры: time set day, list, weather clear, say Hello!</i>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )


@router.message(RconState.waiting_command)
async def on_rcon_input(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    server_id: str = data.get("server_id", "")
    card_message_id: int | None = data.get("card_message_id")
    await state.clear()

    config = SERVERS_BY_ID.get(server_id)
    if not config or not message.text:
        return

    try:
        response = await manager.send_command(config, message.text)
        await message.answer(
            f"<b>Ответ сервера:</b>\n<code>{html.escape(response)}</code>",
            parse_mode="HTML",
        )
    except RCONError as exc:
        await message.answer(
            f"<b>Ошибка RCON:</b>\n<code>{html.escape(str(exc))}</code>",
            parse_mode="HTML",
        )

    # Refresh the server card
    if card_message_id:
        await _render_card(config, bot, message.chat.id, card_message_id)


@router.callback_query(ServerCallback.filter(F.action == "back"))
async def cb_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass


# ---------------------------------------------------------------------------
# Fallback for unrecognised text (not in FSM state)
# ---------------------------------------------------------------------------


@router.message(F.text)
async def on_unknown_text(message: Message) -> None:
    await message.answer(
        "Выбери сервер из меню или воспользуйся /help.",
        reply_markup=main_keyboard(),
    )
