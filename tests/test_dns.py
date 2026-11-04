"""BIND command behavior and failure semantics against strict local-command fakes."""

import subprocess

import pytest

from bind9_aiops.config import TargetConfig
from bind9_aiops.connection import BindCommandError, BindConnection
from bind9_aiops.ops import dns


def _fake_runner(argv, **kwargs):
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is False
    assert isinstance(argv, list)
    if argv == ["rndc", "status"]:
        return subprocess.CompletedProcess(argv, 0, "version: BIND 9.20\n", "")
    if argv == ["rndc", "zonestatus", "example.org"]:
        return subprocess.CompletedProcess(argv, 0, "serial: 2026110401\n", "")
    if argv == ["rndc", "validation", "status"]:
        return subprocess.CompletedProcess(argv, 0, "dnssec-validation is enabled\n", "")
    if argv == ["named-checkconf", "-z"]:
        return subprocess.CompletedProcess(
            argv, 0, "zone example.org/IN: loaded serial 2026110401\n", ""
        )
    if argv[:2] == ["dig", "@127.0.0.1"] and argv[4:6] == ["example.org", "SOA"]:
        return subprocess.CompletedProcess(
            argv,
            0,
            ";; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 1\n"
            "example.org.\t300\tIN\tSOA\tns.example.org. "
            "hostmaster.example.org. 2026110401 3600 900 604800 300\n",
            "",
        )
    if argv[:2] == ["dig", "@192.0.2.2"] and argv[4:6] == ["example.org", "SOA"]:
        return subprocess.CompletedProcess(
            argv,
            0,
            ";; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 2\n"
            "example.org.\t300\tIN\tSOA\tns.example.org. "
            "hostmaster.example.org. 2026110400 3600 900 604800 300\n",
            "",
        )
    raise AssertionError(f"Unexpected command {argv}")


def test_soa_comparison_reports_actual_serial_mismatch():
    conn = BindConnection(TargetConfig("lab"), runner=_fake_runner)
    result = dns.compare_soa(conn, "example.org", "192.0.2.2")
    assert result["primarySerial"] == 2026110401
    assert result["secondarySerial"] == 2026110400
    assert result["serialsMatch"] is False


def test_zone_and_config_commands_use_fixed_argument_lists():
    conn = BindConnection(TargetConfig("lab"), runner=_fake_runner)
    assert "serial" in dns.zone_status(conn, "example.org")["output"]
    assert "loaded" in dns.config_check(conn)["output"]
    with pytest.raises(ValueError):
        dns.zone_status(conn, "example.org; rm -rf /")


def test_servfail_soa_is_unknown_not_matching_zero():
    def runner(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, ";; ->>HEADER<<- status: SERVFAIL, id: 2\n", "")

    conn = BindConnection(TargetConfig("lab"), runner=runner)
    result = dns.compare_soa(conn, "example.org", "192.0.2.2")
    assert result["primarySerial"] is None
    assert result["secondarySerial"] is None
    assert result["serialsMatch"] is None


def test_failed_rndc_is_error_and_partial_diagnosis_is_incomplete():
    def runner(argv, **kwargs):
        if argv[:2] == ["rndc", "zonestatus"]:
            return subprocess.CompletedProcess(argv, 1, "", "zone not loaded")
        return _fake_runner(argv, **kwargs)

    conn = BindConnection(TargetConfig("lab"), runner=runner)
    with pytest.raises(BindCommandError, match="zone not loaded"):
        dns.zone_status(conn, "example.org")
    result = dns.diagnose(conn, "example.org")
    assert result["complete"] is False
    assert result["failedProbes"] == ["zone"]
    assert result["probes"]["zone"]["data"] is None


def test_missing_command_is_teaching_error():
    def runner(argv, **kwargs):
        raise FileNotFoundError(argv[0])

    conn = BindConnection(TargetConfig("lab"), runner=runner)
    with pytest.raises(BindCommandError, match="install bind9 utilities"):
        dns.status(conn)


def test_additional_read_commands_use_official_rndc_argv():
    seen = []

    def runner(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, "status: enabled\n", "")

    conn = BindConnection(TargetConfig("lab"), runner=runner)
    dns.dnssec_zone_status(conn, "example.org")
    dns.managed_keys_status(conn)
    dns.serve_stale_status(conn)
    dns.show_zone(conn, "example.org")
    assert seen == [
        ["rndc", "dnssec", "-status", "example.org"],
        ["rndc", "managed-keys", "status"],
        ["rndc", "serve-stale", "status"],
        ["rndc", "showzone", "example.org"],
    ]


def test_fetch_limits_security_roots_tcp_timeouts_and_signing_are_read_only():
    seen = []

    def runner(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, "current status\n", "")

    conn = BindConnection(TargetConfig("lab"), runner=runner)
    assert dns.fetch_limits(conn)["output"] == "current status\n"
    dns.security_roots(conn)
    dns.tcp_timeouts(conn)
    dns.signing_status(conn, "example.org")
    assert seen == [
        ["rndc", "fetchlimit"], ["rndc", "secroots", "-"],
        ["rndc", "tcp-timeouts"], ["rndc", "signing", "-list", "example.org"],
    ]
    with pytest.raises(ValueError, match="Invalid DNS name"):
        dns.signing_status(conn, "example.org;bad")


def test_reload_zone_dry_run_only_reads_and_acceptance_is_unknown(monkeypatch, tmp_path):
    from bind9_aiops.governance.audit import reset_engine
    from bind9_aiops.mcp_server.tools import dns as tools

    seen = []

    def runner(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, "zone reload queued\n", "")

    conn = BindConnection(TargetConfig("lab"), runner=runner)
    monkeypatch.setattr(tools, "_get_connection", lambda target=None: conn)
    monkeypatch.setenv("BIND9_AIOPS_HOME", str(tmp_path))
    reset_engine()
    try:
        preview = tools.bind_reload_zone("example.org", dry_run=True)
        assert preview["dryRun"] is True
        assert ["rndc", "reload", "example.org"] not in seen
        result = tools.bind_reload_zone("example.org")
        assert result["outcomeUnknown"] is True
        assert ["rndc", "reload", "example.org"] in seen
    finally:
        reset_engine()


def test_reload_timeout_is_unknown_but_definite_rejection_is_error(monkeypatch, tmp_path):
    from bind9_aiops.governance.audit import reset_engine
    from bind9_aiops.mcp_server.tools import dns as tools

    failure = "timeout"

    def runner(argv, **kwargs):
        if argv[:2] == ["rndc", "reload"]:
            if failure == "timeout":
                raise subprocess.TimeoutExpired(argv, 10)
            return subprocess.CompletedProcess(argv, 1, "", "permission denied")
        return subprocess.CompletedProcess(argv, 0, "ok\n", "")

    conn = BindConnection(TargetConfig("lab"), runner=runner)
    monkeypatch.setattr(tools, "_get_connection", lambda target=None: conn)
    monkeypatch.setenv("BIND9_AIOPS_HOME", str(tmp_path))
    reset_engine()
    try:
        assert tools.bind_reload_zone("example.org")["outcomeUnknown"] is True
        failure = "rejected"
        result = tools.bind_reload_zone("example.org")
        assert "permission denied" in result["error"]
        assert "outcomeUnknown" not in result
    finally:
        reset_engine()
