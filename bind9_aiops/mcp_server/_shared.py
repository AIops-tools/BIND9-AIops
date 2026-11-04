"""Shared BIND 9 MCP server and sanitized command errors."""

from __future__ import annotations

import functools
import logging
import threading
from collections.abc import Callable
from typing import Any, Optional

from mcp.server import MCPServer

from bind9_aiops import __version__
from bind9_aiops.connection import BindCommandError, BindWriteUncertainError, ConnectionManager
from bind9_aiops.governance import mark_unknown, sanitize

logger = logging.getLogger(__name__)
_ERROR_MAX = 800


def tool_errors(shape: str = "dict") -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.error("Tool %s failed", func.__name__, exc_info=True)
                message = (
                    sanitize(str(exc), _ERROR_MAX)
                    if isinstance(
                        exc, (BindCommandError, ValueError, KeyError, FileNotFoundError, OSError)
                    )
                    else f"{type(exc).__name__}: operation failed."
                )
                payload = {
                    "error": message,
                    "hint": "Run 'bind9-aiops doctor' and check local command permissions.",
                }
                if isinstance(exc, BindWriteUncertainError):
                    return mark_unknown(payload)
                return payload

        return wrapper

    return decorator


mcp = MCPServer(
    "bind9-aiops",
    version=__version__,
    instructions=(
        "Governed BIND 9 DNS and zone diagnosis using rndc, named-checkconf and dig. "
        "Every tool is audited and budgeted."
    ),
)
_manager: Optional[ConnectionManager] = None
_lock = threading.Lock()


def _get_connection(target: Optional[str] = None) -> Any:
    global _manager
    with _lock:
        if _manager is None:
            _manager = ConnectionManager()
        manager = _manager
    return manager.connect(target)
