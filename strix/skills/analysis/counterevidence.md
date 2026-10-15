---
name: counterevidence
description: Before filing any finding, argue the strongest case against it and set confidence honestly
---

# Counterevidence Pass

Run this before filing any finding. It is the discipline that separates a real audit finding from a plausible-sounding guess.

## Argue against yourself

Write the strongest case that the finding is **not** a vulnerability:

- **Is the guard there?** Read every `require`, `if-revert`, modifier, and access check on the attacker-reachable path. If a control runs on every path before the sink, the finding is `ruled_out`, not `confirmed`.
- **Is the state reachable?** Can an unprivileged actor actually reach the vulnerable state in a live deployment, or does it require a privileged setup outside normal operation?
- **Is it self-harm only?** An attacker who can only hurt themselves is not a finding.
- **Is it a documented tradeoff?** Rounding dust, MEV, and first-depositor `MINIMUM_LIQUIDITY` are standard; flag only if they compound or zero out.
- **Is it admin-by-design?** "Admin can rug" without a concrete mechanism and an unprivileged amplifier is not a finding.

## Record it

- Put the strongest counterargument in the finding's `counterevidence` field.
- Set `confidence` honestly:
  - `high` — a working PoC, or a complete source→control→sink→impact trace that is reachable by an unprivileged actor.
  - `medium` — a static-only trace you could not execute, or a reachable path with an unproven step.
  - `low` — plausible but missing a required piece; usually a lead, not a finding.
- State **what evidence would change the severity** (a specific test, a specific value, a specific deployment fact).

## Default to LEAD when proof is missing

A finding without a concrete proof is a LEAD (`analysis/finding-contract`). That is not a demotion to be avoided — a surfaced lead is worth more than a dropped one. Missing information is never proof of safety.

## Do not let a finding die on a guess

If your counterargument is speculative — "probably wouldn't happen", "the caller would notice" — it **clears** the finding; do not use it to reject. Only a specific, located, code-backed control rejects.
