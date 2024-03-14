from dataclasses import dataclass, field
from enum import Enum


class ServerStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


@dataclass
class PlayerInfo:
    name: str


@dataclass
class ServerInfo:
    status: ServerStatus
    players_online: int = 0
    players_max: int = 0
    players: list[PlayerInfo] = field(default_factory=list)
