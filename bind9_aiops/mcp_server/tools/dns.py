"""Governed BIND 9 read tools."""

from typing import Optional

from bind9_aiops.governance import governed_tool
from bind9_aiops.mcp_server._shared import _get_connection, mcp, tool_errors
from bind9_aiops.ops import dns


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_status(target: Optional[str] = None) -> dict:
    """[READ] Get named service status from rndc."""
    return dns.status(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_config_check(target: Optional[str] = None) -> dict:
    """[READ] Validate BIND config and loaded zone files with named-checkconf -z."""
    return dns.config_check(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_zone_status(zone: str, target: Optional[str] = None) -> dict:
    """[READ] Get BIND's live zonestatus for one zone."""
    return dns.zone_status(_get_connection(target), zone)


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_dnssec_validation(target: Optional[str] = None) -> dict:
    """[READ] Check current DNSSEC validation setting using rndc."""
    return dns.dnssec_status(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_query(name: str, rrtype: str = "A", target: Optional[str] = None) -> dict:
    """[READ] Query the configured DNS server and expose its actual response code."""
    return dns.query(_get_connection(target), name, rrtype)


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_compare_soa(zone: str, secondary: str, target: Optional[str] = None) -> dict:
    """[READ] Compare primary and secondary SOA serials; unknown stays null."""
    return dns.compare_soa(_get_connection(target), zone, secondary)


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_diagnose_zone(zone: str, target: Optional[str] = None) -> dict:
    """[READ] Correlate named, config, zone, SOA and DNSSEC probes; report failures."""
    return dns.diagnose(_get_connection(target), zone)
