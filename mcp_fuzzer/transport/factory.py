from typing import Optional

from .base import TransportProtocol
from .http import HTTPTransport
from .sse import SSETransport
from .stdio import StdioTransport
from .streamablehttp import StreamableHTTPTransport
from mcp_fuzzer.auth.manager import AuthManager


def create_transport(
    protocol: str, endpoint: str, auth_manager: Optional[AuthManager] = None
) -> TransportProtocol:
    """
    Create a transport instance for the given protocol.

    Args:
        protocol: The protocol to use.
        endpoint: The server endpoint (URL or command).
        auth_manager: The authentication manager to use.

    Returns:
        A transport instance.
    """
    if protocol == "http":
        return HTTPTransport(endpoint, auth_manager)
    elif protocol == "sse":
        return SSETransport(endpoint, auth_manager)
    elif protocol == "stdio":
        return StdioTransport(endpoint, auth_manager)
    elif protocol == "streamablehttp":
        return StreamableHTTPTransport(endpoint, auth_manager)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")
