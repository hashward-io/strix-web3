---
name: fix-solidity-vulnerabilities-with-strix
description: Fix the smart-contract vulnerabilities a Strix audit reported — triage by severity, patch the root cause (not the symptom), and re-run Strix to prove each Foundry proof-of-concept no longer succeeds. Each finding carries `code_locations` with verbatim `fix_before`/`fix_after`, so the patch is derived from the proven exploit. Handles reentrancy, access control, oracle/price manipulation, precision/rounding, accounting, upgradeability, signatures, and the rest of the EVM bug classes. Use after a Strix smart-contract audit reports findings, or when the user asks to remediate or patch issues from a `strix_runs` report, `vulnerabilities.json`, or `findings.sarif`.
license: Apache-2.0
metadata:
  author: usestrix
  homepage: https://docs.strix.ai
---

# Fix Solidity vulnerabilities with Strix

Every High/Critical finding from a Strix Web3 audit already carries the exploit and a proposed patch. Remediation is: apply the root-cause fix, then re-run the proof.

## When to use

- A `strix_runs/<run>/` report (or `vulnerabilities.json` / `findings.sarif`) lists findings to fix.
- The user asks to patch, remediate, or resolve smart-contract security issues Strix found.

## Triage

Rank by the tier Strix assigned and by what the PoC demonstrates:

- **Critical / High** — funds at risk, protocol insolvency, or a permissionless state takeover. Fix and re-verify before anything ships.
- **Medium** — a real bug gated by a condition (a specific token, a role, a live oracle). Fix, but confirm the gate.
- **Low / Informational** — hardening and best practice.

Read each finding's `counterevidence` and `confidence` before acting: a `medium`-confidence finding that rests on a static trace may need a PoC first.

## Fix the root cause

Each finding's `code_locations` holds a verbatim `fix_before`/`fix_after`. Apply the root-cause change, not a local patch:

- **Reentrancy** — checks-effects-interactions, then a `nonReentrant` guard on every state-sharing entry point.
- **Access control** — the missing modifier or initializer guard (`_disableInitializers()`), not a caller check at one site.
- **Precision / rounding** — multiply before dividing, round in the protocol's favor, normalize decimals.
- **Accounting** — update aggregate and per-item state atomically (one `_update` helper).
- **Upgradeability** — fix the layout (`__gap` / ERC-7201) or the authorization, not just the one call.

## Verify the fix

1. Re-run the audit against the patched tree: `strix -n -t ./protocol --scan-mode quick`.
2. Confirm the original PoC now fails, and that the fix did not open a new path. The audit's `analysis/fix_verification` skill covers the revert-to-prove step.
3. Re-run the project's own tests: `forge test`.

## Rules

- Only patch code the user is authorized to change.
- Never mark a finding fixed without re-running its proof; a patch that does not break the PoC is not a fix.
