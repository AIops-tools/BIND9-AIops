# Verification — BIND 9 AIops

## Source-backed commands

The [ISC BIND 9 Administrator Reference Manual](https://bind9.readthedocs.io/en/stable/manpages.html), checked 2026-11-04, documents `rndc status`, `rndc zonestatus`, `rndc validation status`, `named-checkconf -z`, and `dig`. The implementation uses those commands without shell interpolation. The [DNSSEC guide](https://bind9.readthedocs.io/en/stable/dnssec-guide.html) documents DNSSEC validation failure modes; this slice reports current status rather than asserting root cause from one response.

## Local verification

`tests/test_dns.py` uses a strict command runner fake. It checks exact argv, no shell, invalid names, SOA mismatch, SERVFAIL-to-null, failed `rndc` and partial diagnosis. Governance invariant tests come from the current tool line. The local result is 121 passing tests, Ruff clean, Bandit Medium+ 0, and a successful source/wheel build on 2026-11-04.

## Not yet live verified

This machine has `dig`, but no `named`, `rndc`, or `named-checkconf`. Docker's daemon was not running. No real BIND daemon, zone file, DNSSEC failure, secondary lag, or write/undo cycle has been tested. Do not call this production validated or published. The next gate is a disposable primary/secondary BIND lab with a deliberately stale secondary and a broken zone, compared with native command output.
