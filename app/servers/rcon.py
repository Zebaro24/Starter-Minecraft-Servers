"""
Minimal async RCON client implementing the Minecraft RCON protocol (Source RCON).
No third-party dependencies — uses only asyncio and struct from the stdlib.
"""

import asyncio
import logging
import struct

logger = logging.getLogger(__name__)

_PACKET_TYPE_AUTH = 3
_PACKET_TYPE_COMMAND = 2


class RCONError(Exception):
    pass


def _encode(request_id: int, packet_type: int, payload: str) -> bytes:
    body = payload.encode("utf-8") + b"\x00\x00"
    header = struct.pack("<iii", len(body) + 8, request_id, packet_type)
    return header + body


def _decode(data: bytes) -> tuple[int, int, str]:
    request_id, packet_type = struct.unpack("<ii", data[:8])
    payload = data[8:-2].decode("utf-8", errors="replace")
    return request_id, packet_type, payload


async def _read_packet(reader: asyncio.StreamReader, timeout: float) -> bytes:
    length_bytes = await asyncio.wait_for(reader.readexactly(4), timeout=timeout)
    length = struct.unpack("<i", length_bytes)[0]
    return await asyncio.wait_for(reader.readexactly(length), timeout=timeout)


async def send_rcon_command(host: str, port: int, password: str, command: str, timeout: float = 5.0) -> str:
    """
    Open a connection, authenticate, send a command, return the response payload.
    Raises RCONError on connection failure, auth failure, or timeout.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except (OSError, asyncio.TimeoutError) as exc:
        raise RCONError(f"Cannot connect to RCON {host}:{port} — {exc}") from exc

    try:
        # Authenticate
        writer.write(_encode(1, _PACKET_TYPE_AUTH, password))
        await writer.drain()

        auth_data = await _read_packet(reader, timeout)
        resp_id, _, _ = _decode(auth_data)
        if resp_id == -1:
            raise RCONError("RCON authentication failed — wrong password")

        # Send command
        writer.write(_encode(2, _PACKET_TYPE_COMMAND, command))
        await writer.drain()

        cmd_data = await _read_packet(reader, timeout)
        _, _, payload = _decode(cmd_data)

        return payload or "(пустой ответ)"

    except asyncio.TimeoutError as exc:
        raise RCONError(f"RCON timed out communicating with {host}:{port}") from exc
    except struct.error as exc:
        raise RCONError(f"RCON protocol error: {exc}") from exc
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except OSError:
            pass
