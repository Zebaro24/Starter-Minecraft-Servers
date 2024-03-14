import logging

import docker
import docker.errors
from mcstatus import JavaServer

from app.config.servers import ServerConfig
from app.servers.models import PlayerInfo, ServerInfo, ServerStatus
from app.servers.rcon import send_rcon_command

logger = logging.getLogger(__name__)


class DockerServerManager:
    """
    Controls Minecraft server Docker containers and queries their state.

    Requires access to the Docker socket (/var/run/docker.sock).
    Each server is identified by its container_name from ServerConfig.
    """

    def __init__(self) -> None:
        self._client = docker.from_env()

    # ------------------------------------------------------------------
    # Container control
    # ------------------------------------------------------------------

    def _get_container(self, container_name: str):
        try:
            return self._client.containers.get(container_name)
        except docker.errors.NotFound:
            return None
        except docker.errors.APIError as exc:
            logger.error("Docker API error for %s: %s", container_name, exc)
            return None

    def get_container_status(self, config: ServerConfig) -> ServerStatus:
        container = self._get_container(config.container_name)
        if container is None:
            return ServerStatus.STOPPED
        mapping = {
            "running": ServerStatus.RUNNING,
            "restarting": ServerStatus.STARTING,
            "created": ServerStatus.STOPPED,
            "exited": ServerStatus.STOPPED,
            "paused": ServerStatus.STOPPED,
            "dead": ServerStatus.STOPPED,
        }
        return mapping.get(container.status, ServerStatus.UNKNOWN)

    def start(self, config: ServerConfig) -> bool:
        container = self._get_container(config.container_name)
        if container is None:
            logger.warning("Container %s not found — cannot start", config.container_name)
            return False
        try:
            container.start()
            logger.info("Container %s started", config.container_name)
            return True
        except docker.errors.APIError as exc:
            logger.error("Failed to start %s: %s", config.container_name, exc)
            return False

    def stop(self, config: ServerConfig) -> bool:
        container = self._get_container(config.container_name)
        if container is None:
            return False
        try:
            container.stop(timeout=60)
            logger.info("Container %s stopped", config.container_name)
            return True
        except docker.errors.APIError as exc:
            logger.error("Failed to stop %s: %s", config.container_name, exc)
            return False

    # ------------------------------------------------------------------
    # Minecraft-level status (mcstatus ping)
    # ------------------------------------------------------------------

    async def get_server_info(self, config: ServerConfig) -> ServerInfo:
        """
        Returns a ServerInfo combining Docker container state and a live mcstatus ping.
        If the container is stopped the ping is skipped.
        If the container is running but the MC server hasn't finished loading yet,
        the ping will fail and we return STARTING.
        """
        docker_status = self.get_container_status(config)

        if docker_status == ServerStatus.STOPPED:
            return ServerInfo(status=ServerStatus.STOPPED)

        if docker_status in (ServerStatus.UNKNOWN,):
            return ServerInfo(status=ServerStatus.UNKNOWN)

        try:
            server = JavaServer(host=config.host, port=config.port, timeout=3)
            status = await server.async_status()
            players: list[PlayerInfo] = []
            if status.players.sample:
                players = [PlayerInfo(name=p.name) for p in status.players.sample]
            return ServerInfo(
                status=ServerStatus.RUNNING,
                players_online=status.players.online,
                players_max=status.players.max,
                players=players,
            )
        except Exception:
            # Container is up but MC hasn't loaded yet
            return ServerInfo(status=ServerStatus.STARTING)

    # ------------------------------------------------------------------
    # RCON
    # ------------------------------------------------------------------

    async def send_command(self, config: ServerConfig, command: str) -> str:
        """Send a command via RCON and return the server's response."""
        return await send_rcon_command(
            host=config.host,
            port=config.rcon_port,
            password=config.rcon_password,
            command=command,
        )
