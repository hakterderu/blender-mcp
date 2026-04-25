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
SOCKET_TIMEOUT = 10.0


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
        object_type: Blender mesh primitive type, e.g. 'CUBE', 'SPHERE', 'PLANE'.
        name: Optional name for the new object.
        location: (x, y, z) world-space location.
        rotation: (rx, ry, rz) Euler rotation in radians.
        scale: (sx, sy, sz) scale factors.
    """
    params: dict[str, Any] = {
        "type": object_type,
        "location": list(location),
        "rotation": list(rotation),
        "scale": list(scale),
    }
    if name:
        params["name"] = name
    return _send_command("create_object", params, host=host, port=port)


def delete_object(name: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """Delete an object from the Blender scene by name."""
    return _send_command("delete_object", {"name": name}, host=host, port=port)


def transform_object(
    name: str,
    location: tuple[float, float, float] | None = None,
    rotation: tuple[float, float, float] | None = None,
    scale: tuple[float, float, float] | None = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict:
    """Apply a transform to an existing object in the scene."""
    params: dict[str, Any] = {"name": name}
    if location is not None:
        params["location"] = list(location)
    if rotation is not None:
        params["rotation"] = list(rotation)
    if scale is not None:
        params["scale"] = list(scale)
    return _send_command("transform_object", params, host=host, port=port)


# ---------------------------------------------------------------------------
# Material tools
# ---------------------------------------------------------------------------

def set_material(
    object_name: str,
    color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    material_name: str | None = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict:
    """Assign a simple diffuse material to an object.

    Args:
        object_name: Name of the target object.
        color: RGBA color values in [0, 1] range.
        material_name: Optional name for the new material.
    """
    params: dict[str, Any] = {
        "object_name": object_name,
        "color": list(color),
    }
    if material_name:
        params["material_name"] = material_name
    return _send_command("set_material", params, host=host, port=port)
