# Verification — BIND 9 AIops

## Source-backed commands

The [ISC BIND 9 Administrator Reference Manual](https://bind9.readthedocs.io/en/stable/manpages.html), checked 2026-11-04, documents `rndc status`, `zonestatus`, `validation status`, `dnssec -status`, `managed-keys status`, `serve-stale status`, `showzone`, `fetchlimit`, `secroots -`, argument-free `tcp-timeouts`, `signing -list`, `reload`, `refresh`, `retransfer`, `notify`, `flushname`, `named-checkconf -z`, and `dig`. The `-` on `secroots` returns output on the RNDC response channel instead of writing a dump file; `tcp-timeouts` with no arguments only displays values. The implementation uses fixed argument lists without shell interpolation. The [DNSSEC guide](https://bind9.readthedocs.io/en/stable/dnssec-guide.html) documents validation failure modes; this tool reports status rather than asserting root cause from one response.

## Local verification

`tests/test_dns.py` uses a strict command runner fake. It checks exact argv for the new read-only commands, no shell, invalid names, SOA mismatch, SERVFAIL-to-null, failed `rndc`, partial diagnosis, retransfer/NOTIFY dry-run no-write, timeout-to-unknown and definite rejection-to-error. Governance invariant tests come from the current tool line. Current result: 126 passing tests, Ruff clean, Bandit 0 Medium+ and wheel/sdist build, rerun on 2026-11-05.

The current 0.2.0 candidate wheel was rebuilt and installed into a new environment outside the source tree; its MCP registry reports 23 tools. Its `retransfer-zone` and `notify-zone` CLI commands ran preview and real calls against strict local `rndc` stand-ins: previews issued no writes, each real call issued exactly one command and exited 2 for unknown completion. An earlier 0.2.0 candidate wheel was also installed outside the source tree; `bind9_aiops.__file__` resolved under `site-packages`. Its CLI ran diagnosis, reload preview and real reload against strict local command stand-ins. The log contained exactly one `rndc reload` (the preview wrote none), and the accepted command exited 2 for unknown outcome. These stand-ins are not a BIND daemon.

## Disposable Linux VM verification (2026-11-08)

Two isolated Debian containers on the `Open-test` Ubuntu VM ran BIND 9.20.30
with the 0.2.0 wheel installed. A real `aiops.test` zone served SOA and A
records. The CLI read live `rndc status`, `zonestatus`, `named-checkconf -z`,
`dig` response codes and a complete zone diagnosis. A reload preview made no
change. A real `reload-zone` request was followed by an independent SOA and
`zonestatus` check: the loaded serial moved from `2026110801` to
`2026110802` and a new A record became queryable. The tool reported
`outcomeUnknown` until that external check, as designed.

An invalid record type in the zone file made config validation fail and
blocked the tool's reload; the daemon's loaded timestamp and answer stayed
unchanged. With a separate secondary, `compare-soa` correctly reported the
primary at serial `2026110803` and the stale secondary at `2026110802`.
`retransfer-zone` was previewed, then executed against the secondary; its SOA
advanced to `2026110803` and comparison returned `serialsMatch: true`. A later
manual `notify-zone` advanced the secondary to `2026110804` when the primary
had `notify explicit` and `also-notify` configured. With NOTIFY disabled, the
same command had been accepted but produced no secondary change, confirming
why acceptance alone is reported as unknown. All configuration changes and
DNS traffic stayed inside disposable containers.
The current suite passed again (126 tests); Ruff and Bandit reported no Medium
or High findings, and wheel/sdist build succeeded.

## Still not live verified

The earlier macOS machine had no `named`, `rndc` or `named-checkconf` and no
working Docker daemon; the Linux VM run above closed the real-daemon and
primary/secondary gaps. DNSSEC validation failure, transfer failure or timeout,
and production resolver behavior remain untested. These writes have no safe
undo. This disposable lab run does not establish production readiness.
