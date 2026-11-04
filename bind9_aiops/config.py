"""Local BIND 9 target configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from bind9_aiops.governance.paths import ops_home


@dataclass(frozen=True)
class TargetConfig:
    name: str
    server: str = "127.0.0.1"
    dns_port: int = 53
    rndc_config: str | None = None
    named_config: str | None = None
    timeout: float = 10.0
    rndc_bin: str = "rndc"
    checkconf_bin: str = "named-checkconf"
    dig_bin: str = "dig"

    def __post_init__(self) -> None:
        if not self.name or not self.server or self.server.startswith("-"):
            raise ValueError("name and server are required; server cannot start with '-'.")
        if not 1 <= self.dns_port <= 65535 or self.timeout <= 0:
            raise ValueError("dns_port must be 1–65535 and timeout must be positive.")
        for binary in (self.rndc_bin, self.checkconf_bin, self.dig_bin):
            if not binary or binary.startswith("-"):
                raise ValueError("Command binaries must be configured by the operator.")


@dataclass(frozen=True)
class AppConfig:
    targets: tuple[TargetConfig, ...] = ()

    def get_target(self, name: str | None = None) -> TargetConfig:
        if name is None:
            if not self.targets:
                raise ValueError("No BIND 9 target configured. Run 'bind9-aiops init'.")
            return self.targets[0]
        for target in self.targets:
            if target.name == name:
                return target
        raise KeyError(f"Unknown BIND 9 target '{name}'.")


def load_config(path: Path | None = None) -> AppConfig:
    path = path or Path(os.environ.get("BIND9_AIOPS_CONFIG", ops_home() / "config.yaml"))
    if not path.is_file():
        raise FileNotFoundError(f"No BIND 9 config at {path}. Run 'bind9-aiops init'.")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or not isinstance(raw.get("targets"), list):
        raise ValueError("BIND 9 config must have a targets list.")
    return AppConfig(tuple(TargetConfig(**entry) for entry in raw["targets"]))
