---
name: differential-review
description: Review a change set or diff for what it breaks — un-updated write sites, moved boundaries, flipped rounding, new early returns, and removed code
---

# Differential Review

A change is guilty until proven safe. Most audit effort looks at the code that *is*; a diff audit looks at what the change *does to* the code around it. The dangerous part of a patch is rarely the new lines in isolation — it is the old assumptions those new lines quietly invalidate. Review the change for what it breaks, not just for what it adds.

## Establish scope

- In-scope: the changed files/lines the run was scoped to (see `scan_modes/diff`).
- Context: the rest of the repository, read to understand callers and callees of the change.
- A dependency or unchanged contract a changed file assumes is in scope **for its interaction with the change only**.
- Read the full file, not just the hunk, so the change is understood in its surrounding logic.

## What a change breaks

For every changed hunk, run these checks:

- **Un-updated write sites** — the change alters how a value is computed, but a sibling writer still writes it the old way. Enumerate all writers of each changed variable.
- **Moved boundaries** — an off-by-one at a shifted `<=`/`<`, a changed array index, a new `- 1`. Recompute the boundary cases on both sides.
- **Flipped rounding** — a division/multiplication reordered, a `floor`→`ceil`, a cast direction reversed. Check which party the rounding now favors.
- **New early return** — an added `return`/`continue`/`break` that skips a state write, an event, an authorization check, or a fee accrual the old path performed.
- **Bypassed guard** — a new branch that does not run the modifier/`require` the old path ran; a new caller class that skips a check.
- **Changed trust assumption** — a parameter that used to be trusted is now caller-supplied; a new external call whose return value is used unvalidated; a new callback.
- **Ordering change** — reads hoisted above writes, a check moved after the effect, a fee applied before/after a cap (`analysis/sharp-edges`).
- **New loop / unbounded input** — an added iteration over a caller-sized collection → gas griefing / runtime-limit DoS.
- **Storage / layout change** — a new variable inserted, a type widened, an ordering swap — breaks upgradeable proxies and serialized accounts (`vulnerabilities/upgradeability-proxy`).
- **Reentrancy surface** — an external call added before a state write, or a state write moved after a call.
- **Changed event or external interface** — a reordered struct/event field breaks off-chain consumers and indexers that depend on the old shape.
- **Changed constants / parameters** — a fee, cap, or decimals constant edited in code rather than governance.

## Removed code

The deleted lines matter as much as the added ones:

- What invariant or guard did the removed code enforce, and does something else replace it?
- Was a `require`, an access modifier, a pause, a reentrancy guard, or a validation deleted without a replacement?
- Did a removed fallback/catch become a silent continue?
- Did a removal change default behavior (see `analysis/insecure-defaults`)?
- Is there dead code that was *supposed* to be called and now is not?

## Compare against intent

- Read the commit message / PR description / linked issue. Does the diff do only what it claims?
- Check the spec still holds after the change (`analysis/spec-to-code`).
- Look for opportunistic changes bundled in — they often carry the bug.

## Differential testing

- Run the old and new implementations against the same inputs and diff the outputs (Foundry `ffi`/differential tests, property tests across versions).
- Re-run existing invariant tests against the change; a broken invariant confirms a regression.

## How to apply

1. Read the full changed files, then the diff.
2. Enumerate every variable/state the change touches and every other writer of it.
3. Walk the "what a change breaks" checklist hunk by hunk; walk the "removed code" list line by line.
4. Reach from each changed line to its callers and callees in the unchanged context.
5. File findings against the changed location, state the diff scope, and if the change is clean, say so against the invariants it preserves (`coordination/dedup-and-assembly`).
