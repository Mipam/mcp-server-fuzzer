from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mcp_fuzzer.auth.manager import AuthManager


class TransportProtocol(ABC):
    """Abstract base class for transport protocols."""

    def __init__(self, endpoint: str, auth_manager: Optional[AuthManager] = None):
        self.endpoint = endpoint
        self.auth_manager = auth_manager

    @abstractmethod
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a JSON-RPC request to the server."""
        pass

    @abstractmethod
    async def send_raw(self, payload: Any) -> Any:
        """Send raw payload to the server."""
        pass

    @abstractmethod
    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the server."""
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool with arguments."""
        pass

    async def close(self):
        """Close the transport connection."""
        pass
