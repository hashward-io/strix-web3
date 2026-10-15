---
name: lending
description: Lending and money markets — collateral, liquidation, interest accrual, bad debt, and solvency invariants
---

# Lending / Money Markets

A lending protocol is an accounting system with a solvency invariant and an oracle. Break either and the protocol is insolvent.

## Structure

- **Markets and shares.** Suppliers deposit and receive `cToken`/`aToken`/shares; borrowers receive debt shares. `totalSupply`/`totalBorrows` are indices.
- **Interest accrual.** A borrow index compounds; `totalBorrows` grows with time. Check that the index updates on every state-changing call, in the right order, and that the borrow/supply rates are computed from the utilization ratio consistently.
- **Health factor / LTV.** `health = collateralValue * liquidationThreshold / debtValue`. Check the threshold, the bonus, and the exact inequality (`>=` vs `>`).
- **Liquidation.** Seize collateral, repay debt, apply a bonus; partial vs full liquidation; who can liquidate and at what price.

## Where to look

- **Oracle.** The whole market's solvency depends on the collateral price (see `vulnerabilities/oracle-manipulation`). A spot-price collateral is liquidatable-at-will.
- **Bad debt.** A position whose debt exceeds collateral, with no mechanism to socialize the loss; a liquidation that reverts when the position is underwater (making bad debt permanent).
- **Interest accrual bugs.** Accruing before/after a supply change; an index that grows without updating `totalBorrows` (or vice versa); reserve/fee taken from interest.
- **Liquidation math.** `repayAmount` vs `seizeAmount` rounding; a liquidation that seizes more than the debt+bonus (leaving the borrower a better position) or less (leaving bad debt); the bonus direction.
- **Rounding direction.** Shares-to-mint down, debt-shares up; exchange-rate rounding in the market's favor; a rounding that lets a borrower accrue less debt than owed.
- **Reentrancy.** A liquidation that calls a token/oracle mid-update; read-only reentrancy via a market's `exchangeRate`/`totalAssets`.
- **Isolation mode / e-mode.** Collateral allowed against the wrong debt asset; a debt asset that is also collateral.
- **Flash-loan caveats.** Deposit-as-collateral, borrow, and default in one tx.
- **Interest-rate model.** A kink that can be surpassed to set an absurd rate; a rate that is negative or overflows.

## Attack plan

1. Write the solvency invariant: `Σ collateralValue(thresholded) >= Σ debtValue`.
2. Trace every function that changes collateral, debt, or indices, and confirm both sides update atomically.
3. Attack the oracle (spot price) and the liquidation math (seize/repay rounding).
4. Try to create bad debt: make a position underwater and show the protocol absorbs the loss.
5. Try to accrue debt or shares at the wrong rate.

## Proof

A Foundry PoC: manipulate the oracle and liquidate profitably; or a borrow/repay sequence that leaves free debt or stuck collateral. Quantify the bad debt.

## Fix

Use a manipulation-resistant oracle with full validation; round consistently in the protocol's favor; keep accounting internal and update indices atomically; add a bad-debt/socialization path; cap liquidation bonus; reentrancy-guard the exchange-rate getters that peers read.
