import json
import logging
import uuid
from typing import Any, Dict, List, Optional

import httpx

from .base import TransportProtocol


from mcp_fuzzer.auth.manager import AuthManager


class SSETransport(TransportProtocol):
    """A transport for sending JSON-RPC requests over Server-Sent Events."""

    def __init__(self, url: str, auth_manager: Optional[AuthManager] = None):
        """
        Initialize the SSETransport.

        Args:
            url: The URL of the server.
            auth_manager: The authentication manager to use.
        """
        super().__init__(url, auth_manager)
        self.headers: Dict[str, str] = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }

    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a JSON-RPC request to the server."""
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        return await self.send_raw(payload)

    async def send_raw(self, payload: Any) -> Any:
        """Send a raw payload to the server."""
        headers = self.headers.copy()
        if self.auth_manager:
            auth_headers = self.auth_manager.get_auth_headers(payload.get("method"))
            headers.update(auth_headers)

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", self.endpoint, json=payload, headers=headers, timeout=30.0) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            try:
                                data = json.loads(line[len("data:") :].strip())
                                if "error" in data:
                                    logging.error("Server returned error: %s", data["error"])
                                    raise Exception(f"Server error: {data['error']}")
                                return data.get("result", data)
                            except json.JSONDecodeError:
                                logging.error("Failed to parse SSE data line as JSON")
                                raise
        except httpx.HTTPError as e:
            logging.error(f"HTTP error during request: {e}")
            raise
        except json.JSONDecodeError:
            logging.error("Raw response: %s", response.text)
            raise

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get a list of available tools from the server."""
        response = await self.send_request("tools/list")
        if not isinstance(response, dict) or "tools" not in response:
            logging.warning("Invalid response for tools/list")
            return []
        return response["tools"]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool with arguments."""
        params = {"name": name, "arguments": arguments}
        return await self.send_request("tools/call", params)
