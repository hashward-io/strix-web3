---
name: diff
description: Audit only the changed source files in a pull request, with surrounding code as context
---

# Diff Audit Mode

Overlay mode: audit the change set, using the rest of the repository only as context. Diff scope never replaces the depth mode — it narrows it to changed files.

## Scope

- In-scope files are the changed source files the run was scoped to, in whatever ecosystem they belong to (see the diff-scope block in the task).
- Everything else in the repository is **context**: read it to understand a changed function's callers and callees, but do not audit it unless the change reaches into it.
- A dependency or unchanged module that a changed file assumes is in scope **for its interaction with the change only**.

## Focus

1. For each changed file, read the full file (not just the diff hunk) so the change is understood in its surrounding logic.
2. Establish the invariants the changed code must preserve, and check whether the change breaks any (`analysis/invariant-discovery`).
3. Run the relevant lenses on the change: access-control and first-principles for guard changes, math-precision and boundary for arithmetic changes, invariant for accounting changes, flow-gap/trust-gap for cross-contract changes.
4. Look specifically for what a change tends to break: un-updated write sites, a new branch that skips a check the old path enforced, a rounding direction flipped, an off-by-one at a moved boundary, a missing state write on the new early-return.

## Report

- File findings against the changed lines, with the added/changed code as the location.
- State the diff scope in the report (files reviewed vs context-only).
- If the change is clean, say so against the invariants it preserves.
