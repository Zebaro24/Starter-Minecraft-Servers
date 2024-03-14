"""
Server registry — add or remove Minecraft servers here.

Each ServerConfig maps a Telegram-facing name to a Docker container.
The bot uses the Docker SDK to start/stop containers and mcstatus + RCON
to query and control the running Minecraft process.
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
    # Minecraft game port
    port: int = 25565
    # RCON port (enable with ENABLE_RCON=true in docker-compose)
    rcon_port: int = 25575
    # RCON password — defaults to the global RCON_PASSWORD env var
    rcon_password: str = field(default_factory=lambda: settings.rcon_password)


# ---------------------------------------------------------------------------
# Server list — edit this to add / remove servers
# ---------------------------------------------------------------------------
SERVERS: list[ServerConfig] = [
    ServerConfig(
        id="stoneblock4",
        name="StoneBlock 4",
        container_name="mc-stoneblock4",
        host="mc-stoneblock4",  # Docker service name on the shared network
        port=25565,
        rcon_port=25575,
    ),
    # Example: add another server
    # ServerConfig(
    #     id="survival",
    #     name="Survival",
    #     container_name="mc-survival",
    #     host="mc-survival",
    #     port=25566,
    #     rcon_port=25576,
    # ),
]

# Fast lookup by ID
SERVERS_BY_ID: dict[str, ServerConfig] = {s.id: s for s in SERVERS}
