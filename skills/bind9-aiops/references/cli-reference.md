# CLI reference

`bind9-aiops init`, `doctor`, `status`, `config-check`, `zone-status <zone>`, `dnssec`, `query <name> [rrtype]`, `compare-soa <zone> <secondary>`, and `diagnose <zone>` are the local commands. Use `--target` to choose a configured target. `bind9-aiops mcp` starts the stdio server. CLI DNS operations call the governed MCP twins and are audited.
