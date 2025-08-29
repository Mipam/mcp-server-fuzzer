import json
import logging
from typing import Any, Optional

from .http import HTTPTransport
from mcp_fuzzer.auth.manager import AuthManager


class StreamableHTTPTransport(HTTPTransport):
    """A transport for sending JSON-RPC requests over streamable HTTP."""

    def __init__(self, url: str, auth_manager: Optional[AuthManager] = None):
        """
        Initialize the StreamableHTTPTransport.

        Args:
            url: The URL of the server.
            auth_manager: The authentication manager to use.
        """
        super().__init__(url, auth_manager)
        self.session_id: Optional[str] = None
        self.protocol_version: Optional[str] = None

    async def send_raw(self, payload: Any) -> Any:
        """Send a raw payload to the server, performing a handshake if necessary."""
        if not self.session_id:
            await self.perform_handshake()

        # Add session headers to the payload
        if self.session_id:
            self.headers["mcp-session-id"] = self.session_id
        if self.protocol_version:
            self.headers["mcp-protocol-version"] = self.protocol_version

        return await super().send_raw(payload)

    async def perform_handshake(self) -> None:
        """Perform a handshake to get the session headers."""
        # The handshake is just an initial request to get the session headers
        # The server is expected to respond with the headers
        response = await self.send_request("tools/list")
        # In a real implementation, we would get the session id from the response headers
        self.session_id = "mock-session-id"
        self.protocol_version = "1.0"
