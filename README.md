<!-- mcp-name: io.github.AIops-tools/bind9-aiops -->
# BIND 9 AIops

Governed BIND 9 DNS operations with 23 MCP tools and corresponding CLI commands. It executes `rndc`, `named-checkconf` and `dig` as fixed argument lists without a shell. Every call is audited and budgeted by the bundled governance harness.

## What it checks

- Named service and zone status from `rndc`.
- Configuration and loaded-zone validation with `named-checkconf -z`.
- DNSSEC validation mode.
- Zone DNSSEC signing, managed-key and serve-stale status; running zone configuration where enabled.
- Recursive fetch-limit hits, DNSSEC trust anchors, DNS TCP timeouts and per-zone signing progress.
- DNS queries with their actual DNS response code.
- Queries against a selected secondary server.
- Guarded secondary retransfer and single-zone NOTIFY resend.
- Primary and secondary SOA serial comparison. A failed or unparseable query returns `null`, never a fabricated zero or match.
- `bind_diagnose_zone` keeps individual probe failures visible.

## Setup from source

Requires Python 3.11+, `uv`, and BIND 9 command utilities on the operator host. Run `uv sync --dev`, `uv run bind9-aiops init`, then `uv run bind9-aiops doctor`. A manual `~/.bind9-aiops/config.yaml` can specify paths and a DNS server:

```yaml
targets:
  - name: local
    server: 127.0.0.1
    dns_port: 53
    rndc_config: /etc/bind/rndc.conf
    named_config: /etc/bind/named.conf
    timeout: 10
```

Use `uv run bind9-aiops diagnose example.org` or `uv run bind9-aiops compare-soa example.org 192.0.2.2`. The MCP entry point is `uv run bind9-aiops-mcp`. The process account needs access to its `rndc` key file and BIND config, but no elevated shell is given to the agent.

## Scope and verification

`reload-zone`, `refresh-zone`, `flush-name`, `retransfer-zone` and `notify-zone` support dry-run and two CLI confirmations. RNDC command acceptance does not prove a queued zone reload or transfer completed, so these writes report `outcomeUnknown`; a lost command response does too. No safe undo exists for a cache flush, retransfer, NOTIFY delivery or externally edited zone file. Zone-file editing, DNSSEC key changes and global service restarts remain outside this release. See [verification](docs/VERIFICATION.md). Missing features and live-environment feedback are welcome as issues or PRs.
