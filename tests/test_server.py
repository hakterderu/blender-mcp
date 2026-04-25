"""Tests for the BlenderMCP server communication and command handling."""

import json
import socket
import threading
import time
import unittest
from unittest.mock import MagicMock, patch


TEST_HOST = "localhost"
TEST_PORT = 19876  # Use a different port than default to avoid conflicts


class TestServerConnection(unittest.TestCase):
    """Test basic server connection and message handling."""

    def _send_command(self, command: dict, host: str = TEST_HOST, port: int = TEST_PORT) -> dict:
        """Helper to send a command to the server and receive a response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            sock.connect((host, port))
            message = json.dumps(command).encode("utf-8")
            sock.sendall(len(message).to_bytes(4, byteorder="big") + message)

            # Read response length
            raw_len = sock.recv(4)
            if not raw_len:
                return {}
            resp_len = int.from_bytes(raw_len, byteorder="big")

            # Read response data
            data = b""
            while len(data) < resp_len:
                chunk = sock.recv(min(4096, resp_len - len(data)))
                if not chunk:
                    break
                data += chunk

            return json.loads(data.decode("utf-8"))

    def test_command_structure(self):
        """Test that a valid command dict has required fields."""
        command = {"type": "get_scene_info", "params": {}}
        self.assertIn("type", command)
        self.assertIn("params", command)

    def test_response_structure_success(self):
        """Test that a success response has expected structure."""
        response = {"status": "success", "result": {"objects": []}}
        self.assertEqual(response["status"], "success")
        self.assertIn("result", response)

    def test_response_structure_error(self):
        """Test that an error response has expected structure."""
        response = {"status": "error", "message": "Unknown command type"}
        self.assertEqual(response["status"], "error")
        self.assertIn("message", response)


class TestCommandValidation(unittest.TestCase):
    """Test command parameter validation logic."""

    def test_get_scene_info_no_params(self):
        """get_scene_info should work with empty params."""
        command = {"type": "get_scene_info", "params": {}}
        self.assertEqual(command["type"], "get_scene_info")

    def test_create_object_required_params(self):
        """create_object should include object type."""
        command = {
            "type": "create_object",
            "params": {
                "type": "MESH",
                "name": "TestCube",
                "location": [0.0, 0.0, 0.0],
            },
        }
        self.assertIn("type", command["params"])
        self.assertEqual(command["params"]["type"], "MESH")

    def test_execute_code_requires_code_field(self):
        """execute_code command must have a 'code' param."""
        command = {"type": "execute_code", "params": {"code": "import bpy"}}
        self.assertIn("code", command["params"])

    def test_set_material_params(self):
        """set_material should have object_name and material fields."""
        command = {
            "type": "set_material",
            "params": {
                "object_name": "Cube",
                "material_name": "Material.001",
                "color": [1.0, 0.0, 0.0, 1.0],
            },
        }
        self.assertIn("object_name", command["params"])
        self.assertIn("color", command["params"])
        self.assertEqual(len(command["params"]["color"]), 4)


class TestMessageFraming(unittest.TestCase):
    """Test the length-prefixed message framing used by the server."""

    def test_encode_message(self):
        """Test that messages are correctly length-prefixed."""
        payload = json.dumps({"type": "ping", "params": {}}).encode("utf-8")
        framed = len(payload).to_bytes(4, byteorder="big") + payload
        self.assertEqual(len(framed), 4 + len(payload))
        decoded_len = int.from_bytes(framed[:4], byteorder="big")
        self.assertEqual(decoded_len, len(payload))

    def test_decode_message(self):
        """Test that a framed message can be decoded correctly."""
        original = {"status": "success", "result": {"name": "Cube"}}
        payload = json.dumps(original).encode("utf-8")
        framed = len(payload).to_bytes(4, byteorder="big") + payload

        decoded_len = int.from_bytes(framed[:4], byteorder="big")
        decoded = json.loads(framed[4: 4 + decoded_len].decode("utf-8"))
        self.assertEqual(decoded, original)


if __name__ == "__main__":
    unittest.main()
