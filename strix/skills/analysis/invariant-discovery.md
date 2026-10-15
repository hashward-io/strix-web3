---
name: invariant-discovery
description: Systematically synthesize a protocol's invariants — conservation, bounds, ratios, state machines, temporal, cross-contract, economic
---

# Invariant Discovery

Terminology: a **guard** is a per-call precondition at a single call site (`require(amount >= MIN)`); it is not a falsifiable invariant. An **invariant** is a property that must hold globally across any sequence of calls. Guards feed the enforced-guards reference; lifted guards and NatSpec claims feed the invariant catalog.

Record every candidate with `record_invariant` (kind, statement, locations, `onchain_enforced`).

## Walk order

1. **Conservation.** Find Δ-pairs in one function body: `Δ(A) = +expr` with `Δ(B) = -expr`, or `mapping[key] += e` with `scalar += e` (⇒ `scalar == Σ mapping[key]`). Verify the pattern holds across **all** functions that write either side; if any writer breaks it, record it as partial conservation with the gap called out. Negative conservation — a flow that ought to track value but touches no storage — is itself an observation.

2. **Guard extraction and lift.**
   - Pass A: every `require`/`assert`/`if-revert` becomes an enforced-guard row, quoted verbatim.
   - Pass B: for each guard, ask whether it implies a property that must hold across calls. If so, rewrite it as a global property and locate **all** write sites of the constrained storage variable. All write sites enforce it → invariant holds on-chain. Any write site does not → the property is unenforced, and that gap is simultaneously an invariant and a likely bug.

3. **Ratio.** For each `A = B * C / D` (with B/C/D storage or storage snapshots), record the ratio and whether the snapshot is taken before or after other writes in the same function (ordering matters).

4. **State machine / one-shot.** For each `require(var == X); ...; var = Y`:
   - one-shot latch (`require(addr == 0); addr = concrete`, no path back) → invariant.
   - togglable flag (another function flips it back) → not a state-machine invariant; skip.
   - cyclic state driven by timing → record as a cycle.

5. **Temporal.** For each `block.timestamp`/`block.number` comparison against storage (deadline, lastUpdate, lockPeriod, interval), extract the constraint and note whether it is checked-then-updated (safe) or updated-then-checked (stale read).

6. **Cross-contract.** For each external call whose return value feeds arithmetic or a storage write, record what the caller assumes; find the callee's write sites; if the callee can change it independently, the assumption is unvalidated. Include setter-vs-invariant mismatches (an admin setter that writes without re-checking an invariant enforced elsewhere).

7. **Economic.** Derive higher-order properties from combinations of the above, citing the specific invariant IDs they build on. A gap in any cited invariant makes the economic invariant unenforced too.

## Verification gate

Before recording any inferred invariant: confirm the Δ-pair / verbatim guard / write-site enumeration / edge / temporal predicate / NatSpec claim actually exists at the cited location. If you cannot verify it, drop it — "could not verify" is not a valid invariant.

## Handoff

- Every invariant feeds the report's invariant section and the fuzzing suite (`custom/fizz-invariants`): each invariant should have a property, or a reason it is not fuzzable.
- Invariants whose write sites are unenforced are the highest-signal leads — a broken invariant is a bug, not a note.
