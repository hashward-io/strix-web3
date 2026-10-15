---
name: deep
description: Multi-pass, invariant-fuzzing smart-contract audit — repeated 12-lens sweeps with a memory ledger plus ecosystem fuzzers
---

# Deep Audit Mode

Exhaustive audit. Maximum coverage, maximum depth. Finding what others miss is the goal.

## Approach

Thorough understanding before exploitation. Test every path, every boundary. Chain findings for maximum impact. Run more than one pass, and each pass after the first is told what the earlier passes found.

## Phase 1 — Exhaustive pre-audit

- Full x-ray (`reconnaissance/x-ray`): architecture, threat model, entry-point classification, git security analysis.
- **Invariant synthesis** — walk the whole taxonomy (`analysis/invariant-discovery`): conservation, guard-lift, ratio, state-machine, temporal, cross-contract, economic. `record_invariant` every candidate with its write sites.
- Protocol-type profiling (`protocols/*`) and composability/dependency mapping.

## Phase 2 — Fuzzing

For invariant-heavy or math-heavy logic, generate and run a fuzzing/invariant suite for the target's ecosystem:

- EVM — Foundry invariant tests for fast properties; Echidna and/or Medusa for stateful invariant fuzzing (`tooling/echidna`, `tooling/medusa`).
- Solana — `anchor test`/LiteSVM harnesses and Trident/`cargo fuzz` for sequences (`tooling/solana-anchor`).
- Move — `sui move test` with `#[expected_failure]` and the Move Prover (`tooling/move-cli`).
- Cairo — `snforge` fuzz tests (`tooling/cairo-scarb`).
- ZK — witness/counterexample search with `nargo`/`snarkjs` (`tooling/zk-circom`, `tooling/zk-noir`).
- Every invariant in the catalog should have a property, or be explicitly marked as not-fuzzable with a reason.

## Phase 3 — Twelve lenses, multiple passes

- Pass 1: all twelve `hacking_agents/*` lenses over the whole in-scope set.
- Record what each pass found (the memory ledger) and feed it to the next pass as "ground already walked."
- Pass 2+: lenses hunt new ground — functions, flows, and mechanisms the earlier passes did not name — and re-confirm prior findings (a re-reached bug is still a bug and is re-reported).

## Phase 4 — Chaining

Individual bugs are starting points. Chain them for maximum impact: information leak → access bypass, oracle manipulation → liquidation cascade, low/medium findings that enable a High. Prefer end-to-end exploit paths over isolated bugs.

## Phase 5 — PoC and closure

- High/Critical: a runnable PoC in the target's ecosystem harness (`custom/poc-construction`) or a complete trace.
- Every candidate closes as `confirmed`, `ruled_out` (with the named control), or `open_proof_gap` — never silently dropped.

## Phase 6 — Reporting

- Deduplicate across passes and lenses; document every confirmed finding with severity, location, impact, PoC, and fix.
- Note areas requiring further review beyond scope.
- Reconcile coverage and invariants, then `finish_scan`.

## Mindset

Relentless. Creative. Patient. Thorough. This is about finding what others miss.
