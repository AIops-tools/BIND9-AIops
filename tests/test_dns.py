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
