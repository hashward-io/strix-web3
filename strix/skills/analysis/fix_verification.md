---
name: fix-verification
description: Derive the concrete fix inline with the finding in any ecosystem, and verify it when a fix is applied
---

# Fix Verification

A report is not complete without a concrete, applicable fix for every confirmed finding whose source is available. Deriving the fix belongs to the reporting agent that reasoned about the root cause — not to a separate downstream pass.

## Deriving the fix

File it inline with `create_vulnerability_report`:

- `code_locations` → the vulnerable location, with `fix_before` (the exact current code) and `fix_after` (the exact corrected code). These must be the real snippet, not a paraphrase.
- Keep the fix minimal and idiomatic: match the codebase's language, version, style, and existing helpers (e.g. SafeERC20/`nonReentrant`/`Math.mulDiv` in Solidity, `checked_*` in Solana, `assert!`/explicit overflow handling in Move/Cairo, `Uint128` math in CosmWasm).
- One finding, one root cause, one fix. If two different fixes are needed, they are two findings.

## Verifying an applied fix

When you also apply the patch in the repo (white-box):

1. Apply the change.
2. Re-run the PoC or the reproduction that proved the bug, in the ecosystem's harness, and confirm it no longer succeeds.
3. Confirm the fix did not break the build or the existing test suite (the ecosystem's build/test command, e.g. `forge test`, `anchor test`, `sui move test`, `scarb test`, `cargo test`).
4. Do this in the same agent/turn while the analysis is fresh — never as a second re-analysis pass.

## Reporting a weak fix

If the honest fix is a mitigation (a cap, a pause, an added check) rather than a full cure, say so and describe the residual risk. A fix that names its own limits is more useful than one that overclaims.
