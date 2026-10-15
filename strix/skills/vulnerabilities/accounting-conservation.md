---
name: accounting-conservation
description: Accounting and conservation — value invented, value lost, double-counting, stale totals, and broken solvency invariants
---

# Accounting and Conservation

At the heart of almost every protocol is a set of accounting identities. If the code lets one be violated, value is created or destroyed.

## The identities to test

- **Solvency** — `totalAssets >= totalDeposits` (for a vault) or `totalCollateral >= totalDebt` (for lending), or `sum(userBalances) == totalSupply` (for a token). State each one and try to break it.
- **Conservation** — value moved between two sides must have equal and opposite deltas. Find every `Δ(A) = +x` / `Δ(B) = -x` pair and confirm no path changes one without the other.
- **Aggregate vs sum-of-parts** — `totalStaked == Σ balances[u]`, `totalShares == Σ shares[u]`, `totalLiquidity == Σ reserves`. Every write site must update both; a function that updates the map but not the total (or vice versa) is the classic bug.
- **Shares/tokens outstanding** — minted must equal burned + outstanding; a mint without a corresponding asset inflow inflates share price or dilutes.

## Where to look

- **Stale totals.** A `totalX` that is not updated when an item is removed (liquidation, burn, withdraw, slashing).
- **Double counting.** An asset counted in two places (collateral and free balance; LP value and underlying).
- **Sync/refresh functions.** `sync()`, `update()`, or a getter that reads `balanceOf(address(this))` and overwrites internal accounting — a donation or a fee-on-transfer token makes the internal number and the real balance diverge.
- **Fee accounting.** Fees taken from `amount` but the full `amount` credited; fees sent to a recipient that also reads `totalAssets`.
- **Debt and interest.** Interest accrues into `totalDebt` but not into the borrower's debt (or vice versa), so repayments leave residue or under-pay.
- **Rounding residue.** Repeated small operations leave a residual unit either in the contract (dust locked) or created (insolvency). Both matter.

## Attack plan

1. Write every accounting identity down explicitly.
2. For each state-changing function, list which sides of each identity it touches; find the function that touches only one side.
3. Look for identities that use `>=` where they should use `==` (a slack that can be exploited) or `==` where rounding makes `>=` necessary (a revert DoS).
4. Try to reach a state where the sum of parts exceeds the total.

## Proof

Name the identity, the function that breaks it, and the resulting surplus or deficit. Quantify it and show whether it repeats. A Foundry invariant test (`sum(balances) == total`) that fails is a strong PoC.

## Fix

Update aggregate and per-item state atomically in every path; prefer internal accounting over raw balances; use a shared `_update` helper; add invariant tests to CI.
