import os
import re
from typing import Any, Dict


from typing import List, Optional, Pattern


class SafetySystem:
    """A system for filtering and sanitizing fuzzer inputs to prevent dangerous operations."""

    def __init__(self, fs_root: Optional[str] = None, no_safety: bool = False):
        """
        Initialize the SafetySystem.

        Args:
            fs_root: The root directory for filesystem sandboxing.
            no_safety: Whether to disable safety filtering.
        """
        self.fs_root = fs_root
        self.no_safety = no_safety
        self.dangerous_patterns: List[str] = [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(--|\b(and|or)\b\s+\d+\s*[=<>]\s*\d+)",
            r"(<script[^>]*>.*?</script>)",
            r"(javascript:.*?)",
            r"(<img[^>]*on\w+\s*=)",
            r"(\.\./|\.\.\\)",
            r"(/etc/passwd|/etc/shadow)",
            r"(c:\\windows\\system32)",
            r"(\b(rm|del|format|shutdown|reboot)\b)",
            r"(\||&|;|`|\$\(|\\n)",
        ]
        self.compiled_patterns: List[Pattern[str]] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns
        ]

    def filter_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter the arguments of a tool call to remove dangerous content.

        Args:
            arguments: The arguments to filter.

        Returns:
            The filtered arguments.
        """
        if self.no_safety:
            return arguments
        return self._sanitize_dict(arguments)

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a dictionary."""
        sanitized = {}
        for key, value in data.items():
            sanitized[key] = self._sanitize_item(value)
        return sanitized

    def _sanitize_list(self, data: List[Any]) -> List[Any]:
        """Sanitize a list."""
        return [self._sanitize_item(item) for item in data]

    def _sanitize_item(self, item: Any) -> Any:
        """Sanitize a single item."""
        if isinstance(item, str):
            return self._sanitize_string(item)
        elif isinstance(item, dict):
            return self._sanitize_dict(item)
        elif isinstance(item, list):
            return self._sanitize_list(item)
        return item

    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string."""
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return "[REDACTED_DANGEROUS_CONTENT]"
        if self.fs_root and ("/" in value or "\\" in value):
             return self._sanitize_path(value)
        return value

    def _sanitize_path(self, path: str) -> str:
        """Sanitize a path to ensure it is within the filesystem sandbox."""
        abs_path = os.path.abspath(os.path.join(self.fs_root, path))
        if os.path.commonprefix([abs_path, self.fs_root]) != self.fs_root:
            return "[REDACTED_DANGEROUS_PATH]"
        return path
