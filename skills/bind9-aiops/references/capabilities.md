# Capabilities

Seven DNS read tools: `bind_status`, `bind_config_check`, `bind_zone_status`, `bind_dnssec_validation`, `bind_query`, `bind_compare_soa`, `bind_diagnose_zone`. Two common governance tools: `undo_list`, `undo_apply`.

Unsupported in this slice: zone updates, reloads, retransfer, cache flush, DNSSEC key rollover, config editing and service restarts. Request missing features with a BIND version and real command output in an issue or PR.
