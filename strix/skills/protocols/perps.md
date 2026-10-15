---
name: perps
description: Perpetuals and derivatives — funding rates, position accounting, liquidation, PnL math, and keeper/oracle interaction
---

# Perpetuals and Derivatives

Perps are the math-heavy corner of DeFi: mark price, index price, funding, margin, and liquidation all interact.

## Math surfaces

- **PnL.** Long/short PnL = `size * (exitPrice - entryPrice) / entryPrice` with the correct sign; unrealized vs realized; a wrong sign flips a profit into a loss or lets a trader mint value.
- **Funding rate.** `fundingRate = clamp(premium + interest)`; accrued to longs or shorts, paid between them; a sign error pays funding to the wrong side; funding that is skipped for positions opened/closed mid-window.
- **Mark vs index.** The mark price (from a pool/oracle) vs the index price; a payer/receiver mismatch; a stale mark that lets a position open at a wrong price.
- **Fees.** `openInterest`, borrowing fee, trading fee, and how they are charged (in the collateral asset, in USD, rounded).
- **Liquidation.** Margin ratio, maintenance margin, liquidation price, partial liquidation, penalty/bonus split; rounding that leaves a residual position or over-seizes.
- **Global vs position.** `openInterestLong == Σ long sizes`, `openInterestShort == Σ short sizes`; a function that updates one without the other breaks funding and skew.
- **Skew and utilization.** Skew-based funding; a skew that can be pushed to an extreme.
- **ADL / socialized loss.** An auto-deleveraging or loss-socialization path whose trigger or distribution is wrong.

## Where to look

- Every `size`/`collateral`/`entryPrice` update in open/increase/decrease/close.
- Funding accrual: is it applied before or after the position change? a position opened and closed within a block paying/receiving funding?
- Liquidation trigger inequality (`>=` vs `>`) and the exact margin formula.
- Oracle interaction: a mark price from a manipulable source (see `vulnerabilities/oracle-manipulation`); the pause/staleness handling.
- Keeper roles: who can execute (liquidate, ADL, update funding) and whether they can grief or extract.

## Attack plan

1. Write PnL, margin, funding, and the `openInterest` identities.
2. Open a position, move the price, and check realized vs expected.
3. Test funding: open before the accrual, close after, see who pays.
4. Test liquidation: force a barely-liquidatable position and check the penalty/residual math.
5. Test skew/oracle manipulation.

## Proof

A Foundry PoC: a sequence of open/price-move/close that extracts more than the price move warrants; a funding payment to the wrong side; a liquidation that over-seizes or leaves free margin. Quantify the extraction.

## Fix

Correct the PnL/funding/margin math with explicit rounding; apply funding and fees atomically with position changes; use manipulation-resistant mark prices; make keeper actions bounded and incentivized; add invariant tests for `openInterest*` and margin.
