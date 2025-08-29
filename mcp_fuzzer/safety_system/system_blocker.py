import os
import stat
from typing import Set, Optional, Any


class SystemBlocker:
    """A context manager for blocking dangerous system commands."""

    def __init__(self):
        """Initialize the SystemBlocker."""
        self.blocked_commands: Set[str] = {
            "rm",
            "del",
            "format",
            "fdisk",
            "mkfs",
            "shutdown", "reboot", "halt", "poweroff",
            "kill", "killall", "pkill", "xkill",
            "iptables", "firewall-cmd", "ufw",
            "apt",
            "yum",
            "dnf",
            "pacman",
            "brew",
        }
        self.original_path: Optional[str] = os.environ.get("PATH")
        self.safe_path_dir: str = "/tmp/mcp_fuzzer_safe_path"

    def __enter__(self) -> None:
        """Enter the context, creating the safe PATH."""
        os.makedirs(self.safe_path_dir, exist_ok=True)
        for cmd in self.blocked_commands:
            fake_cmd_path = os.path.join(self.safe_path_dir, cmd)
            with open(fake_cmd_path, "w") as f:
                f.write(
                    f"#!/bin/sh\necho 'Command \"{cmd}\" is blocked by MCP Fuzzer safety system.'\nexit 1"
                )
            os.chmod(fake_cmd_path, stat.S_IRWXU)
        os.environ["PATH"] = f"{self.safe_path_dir}:{self.original_path}"

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context, restoring the original PATH."""
        os.environ["PATH"] = self.original_path or ""
        for cmd in self.blocked_commands:
            os.remove(os.path.join(self.safe_path_dir, cmd))
        os.rmdir(self.safe_path_dir)
