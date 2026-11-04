"""BIND 9 AIops CLI; each server operation calls its governed MCP twin."""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer
import yaml

from bind9_aiops.cli._common import cli_errors, console, governed
from bind9_aiops.cli.undo import undo_app
from bind9_aiops.governance.paths import ops_home

app = typer.Typer(name="bind9-aiops", no_args_is_help=True, help="Audited BIND 9 DNS diagnosis.")
app.add_typer(undo_app, name="undo")
Target = Annotated[str | None, typer.Option("--target", "-t", help="Configured BIND 9 target")]


def _print(result: dict) -> None:
    console.print_json(json.dumps(governed(result)))


@app.command("init")
@cli_errors
def init() -> None:
    """Configure a local BIND 9 service target."""
    name = typer.prompt("Target name", default="local")
    server = typer.prompt("DNS server address", default="127.0.0.1")
    from bind9_aiops.config import TargetConfig

    chosen = TargetConfig(name=name, server=server)
    path = ops_home() / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f"Config already exists at {path}; edit it to add a target.")
    path.write_text(yaml.safe_dump({"targets": [{"name": chosen.name, "server": chosen.server}]}))
    path.chmod(0o600)
    console.print(f"Configured {name} at {path}")


@app.command("status")
@cli_errors
def status(target: Target = None) -> None:
    """Show named status."""
    from bind9_aiops.mcp_server.tools.dns import bind_status

    _print(bind_status(target=target))


@app.command("config-check")
@cli_errors
def config_check(target: Target = None) -> None:
    """Validate config and zone files."""
    from bind9_aiops.mcp_server.tools.dns import bind_config_check

    _print(bind_config_check(target=target))


@app.command("zone-status")
@cli_errors
def zone_status(zone: str, target: Target = None) -> None:
    """Show live zone status."""
    from bind9_aiops.mcp_server.tools.dns import bind_zone_status

    _print(bind_zone_status(zone=zone, target=target))


@app.command("dnssec")
@cli_errors
def dnssec(target: Target = None) -> None:
    """Show DNSSEC validation status."""
    from bind9_aiops.mcp_server.tools.dns import bind_dnssec_validation

    _print(bind_dnssec_validation(target=target))


@app.command("query")
@cli_errors
def query(name: str, rrtype: str = "A", target: Target = None) -> None:
    """Query a DNS record."""
    from bind9_aiops.mcp_server.tools.dns import bind_query

    _print(bind_query(name=name, rrtype=rrtype, target=target))


@app.command("compare-soa")
@cli_errors
def compare_soa(zone: str, secondary: str, target: Target = None) -> None:
    """Compare primary and secondary SOA serials."""
    from bind9_aiops.mcp_server.tools.dns import bind_compare_soa

    _print(bind_compare_soa(zone=zone, secondary=secondary, target=target))


@app.command("diagnose")
@cli_errors
def diagnose(zone: str, target: Target = None) -> None:
    """Diagnose a BIND 9 zone."""
    from bind9_aiops.mcp_server.tools.dns import bind_diagnose_zone

    _print(bind_diagnose_zone(zone=zone, target=target))


@app.command("doctor")
@cli_errors
def doctor(target: Target = None) -> None:
    """Test access to rndc status."""
    from bind9_aiops.mcp_server.tools.dns import bind_status

    _print(bind_status(target=target))


@app.command("mcp")
@cli_errors
def mcp_cmd() -> None:
    """Start stdio MCP server."""
    if sys.version_info < (3, 11):
        raise typer.Exit(2)
    from bind9_aiops.mcp_server.server import main

    main()


if __name__ == "__main__":
    app()
