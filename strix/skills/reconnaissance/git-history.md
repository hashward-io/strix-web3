---
name: git-history
description: Mine the repository's git history for security signals — hotspots, dangerous-area changes, late changes, forked deps, tech debt
---

# Git History Analysis

Git history tells you where the risk concentrates: the code that changed most, changed late, or changed dangerously.

## Signals to extract (current branch only)

- **Hotspots** — files with the most churn and the most authors. High churn + value-holding code = high risk.
- **Dangerous-area changes** — commits touching math, accounting, access control, or external calls.
- **Late changes** — code changed shortly before the frozen revision. Late changes to value-holding logic are under-reviewed by definition.
- **Fix candidates** — commits whose messages suggest a bug was fixed around it (a fix is often incomplete or reintroduced elsewhere).
- **Forked dependencies** — vendored/adapted code from another project: the original's audit findings may still apply, and the adaptation may have dropped a mitigation.
- **Tech debt** — TODOs, `FIXME`, disabled code, commented-out guards.
- **Dev patterns** — commit cadence, test co-change rate (a file changed without its tests changing).

## Rules

1. Scope to **HEAD** only. State the analyzed branch and commit in the report. Never describe code from another branch as if it were this one.
2. If the repo is a squashed import (one commit), there is no evolution to describe — say so and skip fix/hotspot analysis.
3. Describe what the **current** code does, not what a past commit "changed."
4. Never claim "commits without tests" from a coverage failure — test co-change rate is file co-modification, not coverage.
5. Cross-reference: connect git signals to the architecture and invariant findings (e.g. a late change to a write site that no longer enforces an invariant).
