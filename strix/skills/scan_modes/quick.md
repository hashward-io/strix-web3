---
name: quick
description: Fast high-signal smart-contract audit — build check, architecture skim, and the three highest-yield lenses
---

# Quick Audit Mode

Fastest useful pass. One sweep, no memory, no fuzzing suite, no multi-pass loop. Goal: the obvious High/Critical bugs and a build+architecture picture, in minutes not hours.

## Phase 1 — Build and map (delegate to one recon agent)

- Detect the ecosystem (`reconnaissance/ecosystem-detection`) and establish a green build with its toolchain (`tooling/*`).
- Enumerate in-scope source files for that ecosystem with the scope rule.
- Build the architecture map and a first threat model (`save_threat_model`).
- Extract the entry-point list and a short invariant list (`record_invariant` for the top conservation/bound/state-machine properties).

## Phase 2 — Three lenses (delegate one agent per lens)

Spawn exactly three lens agents over the whole in-scope set:

1. `hacking_agents/access-control` — unprotected functions, escalation, broken init.
2. `hacking_agents/math-precision` — rounding direction, scale mixing, unchecked casts.
3. `hacking_agents/first-principles` — the unnamed logic bug, implicit assumptions broken.

Load the bug-class skills those lenses point at (`vulnerabilities/*`) only when a concrete bug class is implicated.

## Phase 3 — Report

- File confirmed findings with `create_vulnerability_report`. Attach a runnable PoC (`custom/poc-construction`) or a concrete trace for High/Critical.
- Record coverage for every file touched, including the clean ones.
- Assemble the report and `finish_scan`. State clearly that it was a quick pass and what was not covered (no fuzzing, no deep protocol analysis, no multi-pass loop).
