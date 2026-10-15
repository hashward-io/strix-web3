---
name: standard
description: One full 12-lens Solidity audit pass with architecture, threat model, invariant catalog, and PoC for High/Critical
---

# Standard Audit Mode

One complete pass: recon, invariant catalog, all twelve lenses, PoC for High/Critical, and one combined report.

## Phase 1 — x-ray (delegate to one recon agent)

Produce the pre-audit artifacts: `architecture.json`, `x-ray.md`, `entry-points.md`, `invariants.md`, and `git-security-analysis.json` (see `reconnaissance/x-ray`). Store the threat model (`save_threat_model`) and seed the invariant catalog (`record_invariant`).

## Phase 2 — Twelve lenses (delegate one agent per lens)

Spawn all twelve `hacking_agents/*` lenses over the core subsystem set, in parallel:

math-precision · access-control · economic-security · execution-trace · invariant · periphery · first-principles · asymmetry · boundary · numerical-gap · trust-gap · flow-gap

Each child loads its lens plus `analysis/finding-contract`, `analysis/report-language`, and `analysis/senior-auditor-mindset`. Load `protocols/*` and `vulnerabilities/*` on children where the protocol type or a concrete bug class is implicated.

## Phase 3 — Deduplicate and validate

- Deduplicate by root cause (`group_key` = `Contract | function | bug-class`); convergence of 2+ agents on one area is a signal, not a duplicate.
- Run the four gates in `analysis/judging` on each candidate: attack execution, reachability, trigger, impact.
- For every High/Critical, require a Foundry PoC or a complete trace (`custom/foundry-poc`).

## Phase 4 — Report

- File each confirmed finding with `create_vulnerability_report`, with locations and inline fix.
- Reconcile `list_coverage` and `list_invariants`.
- Assemble one report, deduplicated across all twelve lenses, and `finish_scan`.
