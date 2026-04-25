"""Blender MCP Tool Definitions.

This module defines the MCP tools that can be invoked to control Blender
via the addon socket server running inside Blender.
"""

import json
import socket
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9334
# Increased from 10.0 to give Blender more time on heavy scenes/slow machines
SOCKET_TIMEOUT = 30.0


def _send_command(command: str, params: dict[str, Any] | None = None,
                  host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """Send a command to the Blender addon socket server and return the response.

    Args:
        command: The command name to execute.
        params: Optional dictionary of parameters for the command.
        host: The host where Blender is running.
        port: The port the Blender addon is listening on.

    Returns:
        Parsed JSON response from Blender.

    Raises:
        ConnectionRefusedError: If Blender is not running or addon is not active.
        TimeoutError: If Blender does not respond in time.
        ValueError: If the response cannot be parsed.
    """
    payload = {"command": command, "params": params or {}}
    raw = json.dumps(payload).encode("utf-8")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((host, port))
        sock.sendall(raw)
        # Signal end of message
        sock.shutdown(socket.SHUT_WR)

        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)

    response_bytes = b"".join(chunks)
    try:
        return json.loads(response_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response from Blender: {response_bytes!r}") from exc


# ---------------------------------------------------------------------------
# Scene tools
# ---------------------------------------------------------------------------

def get_scene_info(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """Return metadata about the current Blender scene."""
    return _send_command("get_scene_info", host=host, port=port)


def list_objects(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """List all objects in the current Blender scene."""
    return _send_command("list_objects", host=host, port=port)


# ---------------------------------------------------------------------------
# Object tools
# ---------------------------------------------------------------------------

def create_object(
    object_type: str,
    name: str | None = None,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict:
    """Create a new object in the Blender scene.

    Args:
        object_type: Blender mesh primitive type, e.g. '
