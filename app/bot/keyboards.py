from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.config.servers import SERVERS, ServerConfig
from app.servers.models import ServerStatus


class ServerCallback(CallbackData, prefix="srv"):
    action: str  # info | start | stop | rcon | guide | back
    server_id: str = ""


def main_keyboard() -> ReplyKeyboardMarkup:
    """Reply keyboard with one button per server."""
    buttons = [[KeyboardButton(text=s.name)] for s in SERVERS]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, input_field_placeholder="Выбери сервер...")


def server_card_keyboard(config: ServerConfig, status: ServerStatus) -> InlineKeyboardMarkup:
    """Inline keyboard for a server card. Buttons depend on current status."""
    cb = ServerCallback

    refresh_row = [
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=cb(action="info", server_id=config.id).pack(),
            style="primary",
        )
    ]

    if status == ServerStatus.RUNNING:
        action_row = [
            InlineKeyboardButton(
                text="⛔ Остановить",
                callback_data=cb(action="stop", server_id=config.id).pack(),
                style="danger",
            ),
            InlineKeyboardButton(
                text="💬 RCON",
                callback_data=cb(action="rcon", server_id=config.id).pack(),
            ),
        ]
    elif status == ServerStatus.STOPPED:
        action_row = [
            InlineKeyboardButton(
                text="▶️ Запустить",
                callback_data=cb(action="start", server_id=config.id).pack(),
                style="success",
            ),
        ]
    else:
        # STARTING / STOPPING / UNKNOWN — only refresh available
        action_row = []

    guide_row = (
        [
            InlineKeyboardButton(
                text="📖 Инструкции",
                callback_data=cb(action="guide", server_id=config.id).pack(),
            )
        ]
        if config.instructions
        else []
    )

    back_row = [
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=cb(action="back").pack(),
        )
    ]

    rows = [refresh_row]
    if action_row:
        rows.append(action_row)
    if guide_row:
        rows.append(guide_row)
    rows.append(back_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=ServerCallback(action="back").pack(),
                    style="danger",
                )
            ]
        ]
    )
