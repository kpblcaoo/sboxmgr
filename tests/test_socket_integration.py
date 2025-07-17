"""Integration test: Go server + Python client."""

import os
import subprocess

# Add sboxmgr to path
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent / "src"))

from sboxmgr.agent.ipc.socket_client import SocketClient


class TestSocketIntegration:
    """Integration tests for Go server + Python client."""

    @pytest.fixture
    def temp_socket(self):
        """Create temporary socket path."""
        with tempfile.NamedTemporaryFile(suffix=".sock", delete=False) as tmp:
            socket_path = tmp.name
        yield socket_path
        # Cleanup
        try:
            os.unlink(socket_path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def go_server(self, temp_socket):
        """Start Go server and yield process."""
        # Build Go server
        go_dir = Path(__file__).parent.parent.parent / "sboxagent"
        build_cmd = ["go", "build", "-o", "sboxagent", "./cmd/sboxagent"]

        try:
            subprocess.run(build_cmd, cwd=go_dir, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Failed to build Go server: {e}")

        # Start server
        server_cmd = ["./sboxagent", "--socket", temp_socket]
        process = subprocess.Popen(
            server_cmd, cwd=go_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait for server to start
        time.sleep(2)

        yield process

        # Cleanup
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def test_echo_integration(self, temp_socket, go_server):
        """Test full integration: Go server echo + Python client."""
        # Wait a bit more for server to be ready
        time.sleep(1)

        # Create Python client
        client = SocketClient(temp_socket, timeout=10.0)

        try:
            # Connect
            client.connect()

            # Send event message
            event_data = {
                "type": "test_integration",
                "payload": "hello from python client",
            }
            msg = client.protocol.create_event_message(event_data)
            client.send_message(msg)

            # Receive echo response
            response = client.recv_message()

            # Verify response
            print(f"Response: {response}")  # Debug print
            assert response["type"] == "event"
            # Check that we got a valid response structure
            assert "event" in response
            assert response["id"] == msg["id"]  # Echo should preserve ID

        finally:
            client.close()

    def test_command_integration(self, temp_socket, go_server):
        """Test command message integration."""
        time.sleep(1)

        client = SocketClient(temp_socket, timeout=10.0)

        try:
            client.connect()

            # Send command message
            cmd_data = {"param1": "value1", "param2": 42}
            msg = client.protocol.create_command_message("test_command", cmd_data)
            client.send_message(msg)

            # Receive echo response
            response = client.recv_message()

            # Verify response
            assert response["type"] == "command"
            assert response["command"]["command"] == "test_command"
            assert response["command"]["params"] == cmd_data

        finally:
            client.close()

    def test_multiple_messages(self, temp_socket, go_server):
        """Test multiple message exchange."""
        time.sleep(1)

        client = SocketClient(temp_socket, timeout=10.0)

        try:
            client.connect()

            # Send multiple messages
            messages = [
                client.protocol.create_event_message({"type": "msg1"}),
                client.protocol.create_command_message("cmd1", {"p": 1}),
                client.protocol.create_heartbeat_message(
                    "test-agent", "healthy", 100.0, "1.0.0"
                ),
            ]

            for msg in messages:
                client.send_message(msg)
                response = client.recv_message()

                # Verify echo
                assert response["type"] == msg["type"]
                assert response["id"] == msg["id"]

        finally:
            client.close()

    def test_server_not_running(self, temp_socket):
        """Test client behavior when server is not running."""
        client = SocketClient(temp_socket, timeout=1.0)

        with pytest.raises((ConnectionRefusedError, FileNotFoundError)):
            client.connect()
