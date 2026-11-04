"""Bounded execution of official BIND 9 administrative commands; no shell."""

from __future__ import annotations

import re
import subprocess
from typing import Any

from bind9_aiops.config import AppConfig, TargetConfig, load_config

_DOMAIN = re.compile(r"^(?:[A-Za-z0-9_*-]{1,63}\.)*[A-Za-z0-9_*-]{1,63}\.?$")
_RRTYPES = {"A", "AAAA", "CNAME", "DNSKEY", "DS", "MX", "NS", "RRSIG", "SOA", "TXT"}
_OUTPUT_MAX = 12000


class BindCommandError(Exception):
    pass


def domain(value: str) -> str:
    if not _DOMAIN.fullmatch(value) or value.startswith("-") or ".." in value:
        raise ValueError("Invalid DNS name; use a domain or host name without command options.")
    return value


class BindConnection:
    def __init__(self, target: TargetConfig, runner: Any = subprocess.run) -> None:
        self.target = target
        self._run = runner

    def _command(self, argv: list[str]) -> dict:
        try:
            result = self._run(
                argv, capture_output=True, text=True, timeout=self.target.timeout, check=False
            )
        except FileNotFoundError as exc:
            raise BindCommandError(
                f"Missing BIND command '{argv[0]}'; install bind9 utilities or configure its path."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise BindCommandError(
                f"BIND command '{argv[0]}' timed out after {self.target.timeout:g}s."
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown error")[:800]
            raise BindCommandError(
                f"BIND command '{argv[0]}' failed (exit {result.returncode}): {detail}"
            )
        output = result.stdout or ""
        return {
            "output": output[:_OUTPUT_MAX] + ("…" if len(output) > _OUTPUT_MAX else ""),
            "truncated": len(output) > _OUTPUT_MAX,
        }

    def rndc(self, *arguments: str) -> dict:
        argv = [self.target.rndc_bin]
        if self.target.rndc_config:
            argv.extend(["-c", self.target.rndc_config])
        argv.extend(arguments)
        return self._command(argv)

    def check_config(self) -> dict:
        argv = [self.target.checkconf_bin, "-z"]
        if self.target.named_config:
            argv.append(self.target.named_config)
        return self._command(argv)

    def query(self, name: str, rrtype: str = "SOA", server: str | None = None) -> dict:
        name = domain(name)
        rrtype = rrtype.upper()
        if rrtype not in _RRTYPES:
            raise ValueError(f"Unsupported RR type '{rrtype}'.")
        server = server or self.target.server
        if not server or server.startswith("-") or any(c.isspace() for c in server):
            raise ValueError("Invalid DNS server address.")
        argv = [
            self.target.dig_bin,
            f"@{server}",
            "-p",
            str(self.target.dns_port),
            name,
            rrtype,
            "+tries=1",
            "+time=2",
            "+noall",
            "+comments",
            "+answer",
        ]
        result = self._command(argv)
        match = re.search(r"\bstatus:\s*([A-Z]+)", result["output"])
        result.update(
            {
                "name": name,
                "rrtype": rrtype,
                "server": server,
                "rcode": match.group(1) if match else None,
            }
        )
        return result


class ConnectionManager:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()

    def connect(self, target: str | None = None) -> BindConnection:
        return BindConnection(self.config.get_target(target))
