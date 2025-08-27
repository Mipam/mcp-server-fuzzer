from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class TransportProtocol(ABC):
    """Abstract base class for transport protocols."""

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
