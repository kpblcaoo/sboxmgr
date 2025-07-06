"""Unix socket client for sboxmgr with framed JSON protocol.

TODO: Реализовать подключение к Unix socket, отправку/приём framed JSON сообщений,
интеграцию с CLI-командами и event sender.
"""

import socket
from typing import Optional, Dict, Any

SOCKET_PATH = "/var/run/sboxagent.sock"  # TODO: sync with agent config
PROTOCOL_VERSION = 1
FRAME_HEADER_SIZE = 8
MAX_MESSAGE_SIZE = 1024 * 1024

class SocketClient:
    """Unix socket client for communicating with sboxagent."""
    
    def __init__(self, socket_path: str = SOCKET_PATH):
        """Initialize socket client.
        
        Args:
            socket_path: Path to Unix socket.
            
        """
        self.socket_path = socket_path
        self.sock = None

    def connect(self):
        """Connect to Unix socket."""
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)

    def close(self):
        """Close socket connection."""
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_message(self, message: Dict[str, Any]):
        """Send message through socket.
        
        Args:
            message: Message data to send.
            
        Raises:
            NotImplementedError: Method not yet implemented.
            
        """
        # TODO: framed JSON encode
        raise NotImplementedError

    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from socket.
        
        Returns:
            Received message data or None.
            
        Raises:
            NotImplementedError: Method not yet implemented.
            
        """
        # TODO: framed JSON decode
        raise NotImplementedError

# TODO: интеграция с CLI-командами и event sender
