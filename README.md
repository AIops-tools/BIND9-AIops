<!-- mcp-name: io.github.AIops-tools/bind9-aiops -->
# BIND 9 AIops

Governed, read-only diagnosis for BIND 9 DNS services. This local-first 0.1.0 source tree exposes 7 DNS tools plus `undo_list` and `undo_apply` through MCP, with corresponding CLI commands. It executes `rndc`, `named-checkconf` and `dig` as fixed argument lists without a shell. Every MCP call is audited and budgeted by the bundled governance harness.

## What it checks

- Named service and zone status from `rndc`.
- Configuration and loaded-zone validation with `named-checkconf -z`.
- DNSSEC validation mode.
- DNS queries with their actual DNS response code.
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

This slice performs only reads and validation commands. Zone updates, reloads, DNSSEC key changes and cache flushes are withheld until real BIND versions and recovery paths can be tested. See [verification](docs/VERIFICATION.md). Missing features and live-environment feedback are welcome as issues or PRs.
