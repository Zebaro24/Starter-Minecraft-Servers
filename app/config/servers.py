"""
Server registry — add or remove Minecraft servers here.

Each ServerConfig maps a Telegram-facing name to a Docker container.
The bot uses the Docker SDK to start/stop containers and mcstatus + RCON
to query and control the running Minecraft process.

Public IP resolution priority:
  1. public_ip  — static IP or full domain set manually (e.g. "1.2.3.4" or "play.example.com")
  2. subdomain  — prefix combined with settings.base_domain (e.g. "mc1" + "zebaro.dev" → "mc1.zebaro.dev")
  3. auto_public_ip=True — fetches the server's current public IP automatically
  4. Fallback: internal host (Docker service name, not reachable by players)

description and instructions support HTML formatting (Telegram HTML parse mode).
"""

from dataclasses import dataclass, field

from app.config.settings import settings


@dataclass
class ServerConfig:
    # Unique identifier used in callback data and as Docker service name
    id: str
    # Display name shown in the Telegram bot
    name: str
    # Docker container name (must match docker-compose service/container_name)
    container_name: str
    # Hostname for mcstatus pings and RCON — use Docker service name when on the same network
    host: str
    # Static public IP or domain shown to players — e.g. "1.2.3.4" or "play.example.com"
    public_ip: str = ""
    # Subdomain prefix combined with settings.base_domain to form the address — e.g. "mc1" → "mc1.zebaro.dev"
    subdomain: str = ""
    # Auto-detect the server's current public IP (cached for 5 min); ignored when public_ip or subdomain is set
    auto_public_ip: bool = False
    # Minecraft game port
    port: int = 25565
    # RCON port (enable with ENABLE_RCON=true in docker-compose)
    rcon_port: int = 25575
    # RCON password — defaults to the global RCON_PASSWORD env var
    rcon_password: str = field(default_factory=lambda: settings.rcon_password)
    # Short description of the modpack/server shown in the card (HTML allowed)
    description: str = ""
    # Installation/setup instructions shown via the 📖 button (HTML allowed)
    instructions: str = ""


# ---------------------------------------------------------------------------
# Server list — edit this to add / remove servers
# ---------------------------------------------------------------------------
SERVERS: list[ServerConfig] = [
    ServerConfig(
        id="stoneblock4",
        name="⛏️ StoneBlock 4 🪨",
        container_name="mc-stoneblock4",
        host="mc-stoneblock4",  # Docker service name on the shared network
        subdomain="mc1",
        port=25565,
        rcon_port=25575,
        description=(
            "🪨 <b>FTB StoneBlock 4</b> — технический модпак, где ты начинаешь в мире из камня.\n"
            "Добывай ресурсы, строй автоматические фермы и прокачивай базу через систему квестов."
        ),
        instructions=(
            "📦 <b>Как установить FTB StoneBlock 4 (v1.8.0)</b>\n\n"
            "1. Скачай лаунчер CurseForge: "
            '<a href="https://www.curseforge.com/download/app">curseforge.com/download/app</a>\n'
            "2. Установи и запусти лаунчер, войди в аккаунт Minecraft\n"
            "3. Слева выбери <b>Minecraft</b> → <b>Browse Modpacks</b>\n"
            "4. В поиске введи <b>«FTB StoneBlock 4»</b>\n"
            "5. Справа от кнопки <b>Install</b> нажми на стрелочку ▼ и выбери версию <b>1.8.0</b>\n"
            "6. Дождись загрузки, затем нажми <b>Play</b>\n"
            "7. В игре: <b>Multiplayer → Add Server</b> → вставь IP сервера\n\n"
            "⚙️ <b>Требования:</b> Java 21 (ставится автоматически), ОЗУ ≥ 6 ГБ\n"
            "⚠️ <b>Важно:</b> сервер работает только на версии 1.8.0 — не обновляй пак!"
        ),
    ),
    # Example: add another server
    # ServerConfig(
    #     id="survival",
    #     name="Survival",
    #     container_name="mc-survival",
    #     host="mc-survival",
    #     subdomain="mc2",               # or: public_ip="1.2.3.4", or: auto_public_ip=True
    #     port=25566,
    #     rcon_port=25576,
    #     description="Ванильный выживач.",
    #     instructions="Установи Minecraft 1.21 и подключайся!",
    # ),
]

# Fast lookup by ID
SERVERS_BY_ID: dict[str, ServerConfig] = {s.id: s for s in SERVERS}
