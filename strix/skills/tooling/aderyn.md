---
name: aderyn
description: Aderyn static analyzer — Rust-based Solidity detector suite, fast triage, and comparison with Slither
---

# Aderyn

Aderyn is a Rust-based static analyzer (Cyfrin) with an AST pass and a set of detectors. It is fast and complements Slither.

## Usage

- `aderyn .` — analyze; writes `report.md` and `report.json`.
- `aderyn . -o report.md` — explicit output.
- `aderyn . --skip-cloc` / `--exclude <path>` — exclude deps/tests.
- `aderyn . --no-snippets` — compact output.

## High-signal detectors

- Access control: unprotected state-changing functions, missing checks.
- ERC-20/721/4626 rule violations (transfer return, `approve` race, decimal handling).
- `delegatecall` to arbitrary/high-risk targets.
- Storage: uninitialized variables, `.push` without bound.
- Reentrancy and state-after-external-call patterns.
- Missing `require` on critical inputs; division before multiplication; unchecked casts.
- Centralization: functions with a single EOA/owner.

## Triage

1. **Same discipline as Slither** (`tooling/slither`): reproduce before believing; treat each hit as a lead.
2. **Cross-reference with Slither.** Aderyn and Slither flag overlapping but non-identical sets; run both and take the union as leads.
3. **Severity** is heuristic — reassign with `analysis/severity-calibration`.
4. **Coverage.** Aderyn reasons about syntax and patterns, not economics, live state, or protocol intent.

## Workflow

1. `forge build` (Aderyn may also compile, but a green build first avoids noise).
2. `aderyn .` → triage the union with Slither's output.
3. Investigate each lead by hand; record confirmed findings and ruled-out leads.

## Pitfalls

- Detector sets differ by version; pin the version in the report.
- Report output can be large; filter to production paths.
