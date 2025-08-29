import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from .base import TransportProtocol


from mcp_fuzzer.auth.manager import AuthManager


class StdioTransport(TransportProtocol):
    """A transport for communicating with a server over stdin/stdout."""

    def __init__(self, command: str, auth_manager: Optional[AuthManager] = None):
        """
        Initialize the StdioTransport.

        Args:
            command: The command to run to start the server.
            auth_manager: The authentication manager to use (not used by this transport).
        """
        super().__init__(command, auth_manager)
        self.process: Optional[asyncio.subprocess.Process] = None

    async def start_server(self) -> None:
        """Start the server subprocess."""
        self.process = await asyncio.create_subprocess_shell(
            self.endpoint,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def stop_server(self) -> None:
        """Stop the server subprocess."""
        if self.process:
            self.process.terminate()
            await self.process.wait()

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
        if not self.process:
            await self.start_server()

        payload_str = json.dumps(payload)
        self.process.stdin.write(payload_str.encode() + b'\n')
        await self.process.stdin.drain()

        response_str = await self.process.stdout.readline()
        if not response_str:
            stderr = await self.process.stderr.read()
            raise ConnectionError(f"No response from server. Stderr: {stderr.decode()}")

        try:
            data = json.loads(response_str)
            if "error" in data:
                logging.error("Server returned error: %s", data["error"])
                raise Exception(f"Server error: {data['error']}")
            return data.get("result", data)
        except json.JSONDecodeError:
            logging.error("Failed to parse response as JSON: %s", response_str)
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

    async def close(self) -> None:
        """Close the transport connection."""
        await self.stop_server()
