---
name: severity-calibration
description: The severity rubric for smart-contract findings — impact, likelihood, and what each tier requires
---

# Severity Calibration

Score only the impact that a PoC or a complete trace demonstrates. Reachability, a scary function name, and "could be exploited" do not set severity on their own.

## Tiers

- **Critical** — direct, repeatable loss or lock of user funds at scale without exotic preconditions; broken accounting that mints value from nothing; a permissionless path to drain a value-holding contract; a protocol-wide invariant broken by a normal call.
- **High** — material loss or DoS with a realistic precondition (a common token behavior, a reachable state, a bounded role abuse with an unprivileged amplifier). A confirmed High needs a working PoC or a complete trace.
- **Medium** — bounded or non-compounding loss, a griefing DoS with clear cost, a broken invariant whose impact is limited, a missing check that requires an unusual but achievable state.
- **Low** — correctness issues with minimal impact, reversible/griefing-only, or a control that is wrong but currently unreachable.
- **Informational** — hygiene, events, NatSpec, gas, naming. Usually not filed as a vulnerability.

## How to choose

1. **Impact first.** Name the victim and the concrete harm (funds lost, funds locked, protocol insolvent, service down). No victim → no High.
2. **Then likelihood.** Is the trigger permissionless, or does it need a bounded role? Admin-only harm is rejected unless the body names a concrete unprivileged amplifier (race, retroactive sweep, asymmetric formula, access gap) — see `analysis/judging`.
3. **Then preconditions.** Common token behaviors (fee-on-transfer, rebasing, blacklisting, void-return) are plausible preconditions for contracts accepting arbitrary tokens; "the admin would never" and "the deployer would set X" are not.
4. **Compounding beats size.** A dust-level bug that compounds across many calls is worse than a one-off dust bug — say so in the impact.

## What sets nothing

Missing events, gas micro-optimizations, naming, NatSpec, and linter output are not findings. Centralization without an exploit path is not a finding.

Every non-trivial impact claim must map to explicit evidence in the report. State the confidence (`analysis/counterevidence`) and what would raise or lower the severity.
