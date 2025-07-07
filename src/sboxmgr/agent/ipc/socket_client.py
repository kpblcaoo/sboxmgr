"""SocketClient for framed JSON protocol over Unix socket.

Usage example:
    from sboxmgr.agent.ipc.socket_client import SocketClient
    client = SocketClient('/tmp/sboxagent.sock')
    client.connect()
    msg = client.protocol.create_event_message({'type': 'ping'})
    client.send_message(msg)
    response = client.recv_message()
    print(response)
    client.close()
"""

import socket
from typing import Any, Dict, Optional

try:
    from sbox_common.protocols.socket.framed_json import FramedJSONProtocol
except ImportError:
    raise ImportError(
        "sbox_common package not found. Please install it with: "
        "pip install -e ../sbox-common"
    )


class SocketClient:
    """Client for framed JSON protocol over Unix socket."""

    def __init__(self, socket_path: str, timeout: float = 5.0):
        """Initialize SocketClient.

        Args:
            socket_path: Path to Unix socket.
            timeout: Connection timeout in seconds.

        """
        self.socket_path = socket_path
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self.protocol = FramedJSONProtocol()

    def connect(self) -> None:
        """Connect to the Unix socket."""
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)

    def send_message(self, message: Dict[str, Any]) -> None:
        """Send a framed JSON message.

        Args:
            message: Message dictionary to send.

        Raises:
            RuntimeError: If socket is not connected.

        """
        if not self.sock:
            raise RuntimeError("Socket is not connected")
        data = self.protocol.encode_message(message)
        self.sock.sendall(data)

    def recv_message(self) -> Dict[str, Any]:
        """Receive a framed JSON message.

        Returns:
            Received message dictionary.

        Raises:
            RuntimeError: If socket is not connected or connection closed.
            ConnectionError: If incomplete data received.

        """
        if not self.sock:
            raise RuntimeError("Socket is not connected")

        # Read frame header
        header = self._recv_exact(self.protocol.FRAME_HEADER_SIZE)
        if len(header) != self.protocol.FRAME_HEADER_SIZE:
            raise ConnectionError(
                f"Connection closed: incomplete header received ({len(header)}/{self.protocol.FRAME_HEADER_SIZE} bytes)"
            )

        length, version = self._unpack_header(header)
        if version != self.protocol.PROTOCOL_VERSION:
            raise RuntimeError(f"Unsupported protocol version: {version}")

        # Read message body
        body = self._recv_exact(length)
        if len(body) != length:
            raise ConnectionError(
                f"Connection closed: incomplete message body received ({len(body)}/{length} bytes)"
            )

        message, _ = self.protocol.decode_message(header + body)
        return message

    def _recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes from the socket.

        Args:
            n: Number of bytes to receive.

        Returns:
            Received bytes (may be less than n if connection closed).

        """
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:  # Connection closed
                break
            buf += chunk
        return buf

    def close(self) -> None:
        """Close the socket connection."""
        if self.sock:
            self.sock.close()
            self.sock = None

    def _unpack_header(self, header: bytes):
        """Unpack frame header.

        Args:
            header: Frame header bytes.

        Returns:
            Tuple of (length, version).

        """
        import struct

        return struct.unpack(">II", header)
