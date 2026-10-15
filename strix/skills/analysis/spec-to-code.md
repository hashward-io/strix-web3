---
name: spec-to-code
description: Extract invariants and promises from the spec, whitepaper, or docs, then verify each against the code and report divergence as a finding
---

# Spec to Code

A protocol is correct only relative to what it promises. The specification — whitepaper, docs, NatSpec, README, an audit report, a governance proposal — states invariants and guarantees the implementation must uphold. Audit the gap. A divergence between a documented promise and the code is a finding even when no classic bug pattern matches, because the users (and integrators) relied on the promise.

## Collect the spec

Gather every authoritative statement of intent, in order of trust:

- Whitepaper / litepaper / design doc in the repo or linked from the README.
- In-code NatSpec (`@notice`, `@dev`, `@param`, `@return`) and doc comments.
- README, `docs/`, `SPEC.md`, `ARCHITECTURE.md`, comments in interfaces.
- Test names and assertions (`test_WithdrawRevertsWhenInsolvent`) — tests encode intent.
- Governance proposals, parameter-change docs, prior audit findings.
- Published parameters (fees, caps, decimals, timelocks) from the deployment/frontend.

If two sources conflict, that conflict is itself a lead: the implementation cannot satisfy both.

## Extract invariants and promises

Turn prose into falsifiable statements. Each must be checkable against the code.

- **Conservation** — "the protocol never holds less than the sum of user balances"; "fees are the only value that leaves the system".
- **Bounds** — "collateralization ratio stays ≥ 100% after any interaction"; "total supply ≤ MAX_SUPPLY".
- **Monotonicity / one-way** — "a proposal cannot be executed twice"; "shares never decrease without a withdrawal".
- **Temporal** — "unbonding takes at least 7 days"; "rewards accrue only after the epoch boundary".
- **Access** — "only the guardian can pause"; "no function mints without governance".
- **Rounding direction** — "rounding always favors the protocol"; "withdrawals round down".
- **Symmetry** — "deposit and withdraw use the same price source".
- **External** — "the oracle is never read for a stale price"; "an upgrade cannot change storage layout".

Tag each with its source (file/line or doc section) so you can quote it. Never invent a quote; if the spec is silent, say so rather than manufacturing a promise.

## Verify each promise in code

For each statement, find the code that enforces it and try to falsify it:

1. Locate the write sites the promise constrains (see `analysis/invariant-discovery`).
2. Check every path, not just the happy one — new branch, early return, admin path, upgrade path.
3. Check the primitive the promise rests on: the same price source, the same unit, the same ordering.
4. If nothing enforces the promise, that is a divergence even if no test fails.

## Categories of divergence

- **Unimplemented promise** — documented behavior with no code path.
- **Partially implemented** — enforced in one function, not in its sibling.
- **Weakened** — a check exists but with a bound/unit/actor different from the spec.
- **Inverted** — the code rounds or defaults opposite to the stated direction.
- **Stale spec** — the code changed and the doc was not updated; still a lead (integrators rely on the doc).

## Attack plan

1. Extract the value-bearing promises first (conservation, bounds, rounding direction).
2. For each, grep the code for the enforcing check and its negation.
3. Try to reach a state that violates the promise with an unprivileged actor.
4. Cross-reference every divergence with `hacking_agents/invariant` and `protocols/*` for the protocol type.

## Proof and severity

The proof is the trace that violates the promise plus the quoted spec line it violates. Severity is set by the impact of the broken promise, not by the fact that it is documented — a doc typo is Informational; a broken conservation invariant is Critical.

## How to apply

1. Read the spec sections once, extracting promises into a list with sources.
2. Verify each promise against the code; record enforced / unenforced / opposite.
3. For every unenforced value-bearing promise, attempt a violation trace and record a LEAD or FINDING.
4. Feed the confirmed invariants into the report's invariant section and the fuzzing suite (`custom/fizz-invariants`).
5. Re-scan after any finding: a broken near-invariant usually breaks its documented form too.
