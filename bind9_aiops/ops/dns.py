"""Read-only BIND 9 diagnostics."""

from __future__ import annotations

import re

from bind9_aiops.connection import BindConnection, domain


def status(conn: BindConnection) -> dict:
    return conn.rndc("status")


def config_check(conn: BindConnection) -> dict:
    return conn.check_config()


def zone_status(conn: BindConnection, zone: str) -> dict:
    return conn.rndc("zonestatus", domain(zone))


def dnssec_status(conn: BindConnection) -> dict:
    return conn.rndc("validation", "status")


def query(conn: BindConnection, name: str, rrtype: str = "A") -> dict:
    return conn.query(name, rrtype)


def _soa_serial(result: dict) -> int | None:
    if result.get("rcode") != "NOERROR" or result.get("truncated"):
        return None
    for line in result["output"].splitlines():
        if line.startswith(";") or "\tSOA\t" not in line:
            continue
        tokens = re.split(r"\s+", line.strip())
        if "SOA" in tokens:
            i = tokens.index("SOA")
            if len(tokens) > i + 3 and tokens[i + 3].isdigit():
                return int(tokens[i + 3])
    return None


def compare_soa(conn: BindConnection, zone: str, secondary: str) -> dict:
    zone = domain(zone)
    if not secondary or secondary.startswith("-") or any(c.isspace() for c in secondary):
        raise ValueError("Invalid secondary DNS server address.")
    primary = conn.query(zone, "SOA")
    other = conn.query(zone, "SOA", secondary)
    p, s = _soa_serial(primary), _soa_serial(other)
    return {
        "zone": zone,
        "primary": primary,
        "secondary": other,
        "primarySerial": p,
        "secondarySerial": s,
        "serialsMatch": p == s if p is not None and s is not None else None,
        "note": (
            "Serials are unknown when a query failed, was truncated or returned no parseable SOA."
        ),
    }


def diagnose(conn: BindConnection, zone: str) -> dict:
    probes = {}
    for name, call in (
        ("service", lambda: status(conn)),
        ("config", lambda: config_check(conn)),
        ("zone", lambda: zone_status(conn, zone)),
        ("soa", lambda: conn.query(zone, "SOA")),
        ("dnssecValidation", lambda: dnssec_status(conn)),
    ):
        try:
            probes[name] = {"data": call(), "error": None}
        except Exception as exc:
            probes[name] = {"data": None, "error": f"{type(exc).__name__}: {exc}"}
    failed = [name for name, probe in probes.items() if probe["error"] is not None]
    return {"zone": zone, "probes": probes, "failedProbes": failed, "complete": not failed}
