# Verification — BIND 9 AIops

## Source-backed commands

The [ISC BIND 9 Administrator Reference Manual](https://bind9.readthedocs.io/en/stable/manpages.html), checked 2026-11-04, documents `rndc status`, `zonestatus`, `validation status`, `dnssec -status`, `managed-keys status`, `serve-stale status`, `showzone`, `fetchlimit`, `secroots -`, argument-free `tcp-timeouts`, `signing -list`, `reload`, `refresh`, `retransfer`, `notify`, `flushname`, `named-checkconf -z`, and `dig`. The `-` on `secroots` returns output on the RNDC response channel instead of writing a dump file; `tcp-timeouts` with no arguments only displays values. The implementation uses fixed argument lists without shell interpolation. The [DNSSEC guide](https://bind9.readthedocs.io/en/stable/dnssec-guide.html) documents validation failure modes; this tool reports status rather than asserting root cause from one response.

## Local verification

`tests/test_dns.py` uses a strict command runner fake. It checks exact argv for the new read-only commands, no shell, invalid names, SOA mismatch, SERVFAIL-to-null, failed `rndc`, partial diagnosis, retransfer/NOTIFY dry-run no-write, timeout-to-unknown and definite rejection-to-error. Governance invariant tests come from the current tool line. Current result: 126 passing tests, Ruff clean, Bandit 0 Medium+ and wheel/sdist build on 2026-11-04.

The current 0.2.0 candidate wheel was rebuilt and installed into a new environment outside the source tree; its MCP registry reports 23 tools. Its `retransfer-zone` and `notify-zone` CLI commands ran preview and real calls against strict local `rndc` stand-ins: previews issued no writes, each real call issued exactly one command and exited 2 for unknown completion. An earlier 0.2.0 candidate wheel was also installed outside the source tree; `bind9_aiops.__file__` resolved under `site-packages`. Its CLI ran diagnosis, reload preview and real reload against strict local command stand-ins. The log contained exactly one `rndc reload` (the preview wrote none), and the accepted command exited 2 for unknown outcome. These stand-ins are not a BIND daemon.

## Not yet live verified

This machine has `dig`, but no `named`, `rndc`, or `named-checkconf`. Docker's daemon was not running. No real BIND daemon, zone file, DNSSEC failure, secondary lag, retransfer or NOTIFY completion, or write cycle has been tested. These commands have no safe undo. Do not call the package production validated. The next gate is a disposable primary/secondary BIND lab with a deliberately stale secondary and a broken zone, compared with native command output.
