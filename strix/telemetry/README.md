### Telemetry

Strix Web3 sends **no telemetry**. This fork is fully local: nothing about your
code, targets, findings, or usage leaves the sandbox.

The `strix.telemetry` package is retained only as a compatibility shim. It keeps
the historical import surface — `report_error`, `set_scan_phase`, and the
`posthog` / `scarf` names — so existing call sites keep working, but every
function is a no-op and performs no network I/O.

`STRIX_TELEMETRY` is accepted for backwards compatibility and has no effect.
