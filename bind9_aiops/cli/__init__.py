"""CLI package for bind9-aiops.

Re-exports ``app`` so the pyproject entry point
``bind9-aiops = "bind9_aiops.cli:app"`` works unchanged.
"""

from bind9_aiops.cli._root import app

__all__ = ["app"]
