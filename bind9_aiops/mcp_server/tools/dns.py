"""Governed BIND 9 read tools."""

from typing import Optional

from bind9_aiops.connection import domain
from bind9_aiops.governance import governed_tool, mark_unknown
from bind9_aiops.mcp_server._shared import _get_connection, mcp, tool_errors
from bind9_aiops.ops import dns


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_fetch_limits(target: Optional[str] = None) -> dict:
    """[READ] Show servers and domains currently limited by recursive fetch caps."""
    return dns.fetch_limits(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_security_roots(target: Optional[str] = None) -> dict:
    """[READ] Show trust anchors through rndc's response channel, without a dump file."""
    return dns.security_roots(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_tcp_timeouts(target: Optional[str] = None) -> dict:
    """[READ] Show current DNS TCP timeouts without changing them."""
    return dns.tcp_timeouts(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_signing_status(zone: str, target: Optional[str] = None) -> dict:
    """[READ] List a zone's ongoing and completed DNSSEC signing state."""
    return dns.signing_status(_get_connection(target), zone)


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_dnssec_zone_status(zone: str, target: Optional[str] = None) -> dict:
    """[READ] Show DNSSEC signing status for one zone."""
    return dns.dnssec_zone_status(_get_connection(target), zone)


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_managed_keys_status(target: Optional[str] = None) -> dict:
    """[READ] Show BIND managed DNSSEC trust-key status."""
    return dns.managed_keys_status(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_serve_stale_status(target: Optional[str] = None) -> dict:
    """[READ] Show whether stale DNS answers are currently served."""
    return dns.serve_stale_status(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_show_zone(zone: str, target: Optional[str] = None) -> dict:
    """[READ] Show a running dynamic zone's configuration when enabled."""
    return dns.show_zone(_get_connection(target), zone)


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def bind_query_server(
    name: str, server: str, rrtype: str = "A", target: Optional[str] = None
) -> dict:
    """[READ] Query a specified DNS server for a supported record type."""
    return dns.query_server(_get_connection(target), name, rrtype, server)


@mcp.tool()
@governed_tool(risk_level="medium")
@tool_errors()
def bind_reload_zone(zone: str, dry_run: bool = False, target: Optional[str] = None) -> dict:
    """[WRITE] Check config and queue a zone reload; completion remains unknown."""
    conn = _get_connection(target)
    zone = domain(zone)
    before = dns.zone_status(conn, zone)
    check = dns.config_check(conn)
    if dry_run:
        return {"dryRun": True, "zone": zone, "before": before, "configCheck": check}
    response = conn.rndc_write("reload", zone)
    return mark_unknown({"accepted": True, "zone": zone, "response": response,
                         "note": "rndc acceptance does not prove the zone finished loading."})


@mcp.tool()
@governed_tool(risk_level="medium")
@tool_errors()
def bind_refresh_zone(zone: str, dry_run: bool = False, target: Optional[str] = None) -> dict:
    """[WRITE] Ask a secondary zone to refresh; transfer completion remains unknown."""
    conn = _get_connection(target)
    zone = domain(zone)
    before = dns.zone_status(conn, zone)
    if dry_run:
        return {"dryRun": True, "zone": zone, "before": before}
    response = conn.rndc_write("refresh", zone)
    return mark_unknown({
        "accepted": True, "zone": zone, "response": response,
        "note": "Check zonestatus and SOA again before claiming transfer success.",
    })


@mcp.tool()
@governed_tool(risk_level="medium")
@tool_errors()
def bind_flush_name(name: str, dry_run: bool = False, target: Optional[str] = None) -> dict:
    """[WRITE] Flush one DNS name from cache; cache state cannot be restored."""
    conn = _get_connection(target)
    name = domain(name)
    dns.status(conn)
    if dry_run:
        return {"dryRun": True, "name": name, "wouldFlush": True}
    response = conn.rndc_write("flushname", name)
    return mark_unknown({"accepted": True, "name": name, "response": response,
                         "note": "The cache entry has no safe undo or observable prior value."})


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
