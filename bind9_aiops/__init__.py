"""BIND 9 AIops: governed read-only DNS operations."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bind9-aiops")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
