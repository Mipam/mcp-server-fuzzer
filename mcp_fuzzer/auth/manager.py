import os
import base64
from typing import Dict, Optional


class AuthManager:
    """Manages authentication providers and credentials."""

    def __init__(self, auth_config: Optional[Dict[str, Any]] = None, use_env: bool = False):
        """
        Initialize the AuthManager.

        Args:
            auth_config: A dictionary containing authentication provider settings.
            use_env: Whether to load authentication settings from environment variables.
        """
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.tool_mappings: Dict[str, str] = {}
        if auth_config:
            self.load_from_config(auth_config)
        if use_env:
            self.load_from_env()

    def load_from_config(self, auth_config: Dict[str, Any]) -> None:
        """Load authentication settings from a configuration dictionary."""
        self.providers = auth_config.get("providers", {})
        self.tool_mappings = auth_config.get("tool_mappings", {})

    def load_from_env(self) -> None:
        """Load authentication settings from environment variables."""
        if "MCP_API_KEY" in os.environ:
            self.providers["env_api_key"] = {
                "type": "api_key",
                "api_key": os.environ["MCP_API_KEY"],
                "header_name": os.environ.get("MCP_HEADER_NAME", "Authorization"),
            }
        if "MCP_USERNAME" in os.environ and "MCP_PASSWORD" in os.environ:
            self.providers["env_basic"] = {
                "type": "basic",
                "username": os.environ["MCP_USERNAME"],
                "password": os.environ["MCP_PASSWORD"],
            }
        if "MCP_OAUTH_TOKEN" in os.environ:
            self.providers["env_oauth"] = {
                "type": "oauth",
                "token": os.environ["MCP_OAUTH_TOKEN"],
            }

    def get_auth_headers(self, tool_name: str) -> Dict[str, str]:
        """
        Get authentication headers for a given tool.

        Args:
            tool_name: The name of the tool.

        Returns:
            A dictionary of authentication headers.
        """
        provider_name = self.tool_mappings.get(tool_name)
        if not provider_name:
            # Fallback to env providers if no specific mapping
            if "env_api_key" in self.providers:
                provider_name = "env_api_key"
            elif "env_basic" in self.providers:
                provider_name = "env_basic"
            elif "env_oauth" in self.providers:
                provider_name = "env_oauth"
            else:
                return {}

        provider = self.providers.get(provider_name)
        if not provider:
            return {}

        auth_type = provider.get("type")
        if auth_type == "api_key":
            header_name = provider.get("header_name", "Authorization")
            api_key = provider.get("api_key")
            return {header_name: f"Bearer {api_key}"}
        elif auth_type == "basic":
            username = provider.get("username")
            password = provider.get("password")
            encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        elif auth_type == "oauth":
            token = provider.get("token")
            return {"Authorization": f"Bearer {token}"}

        return {}
