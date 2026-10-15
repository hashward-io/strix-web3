---
name: mev-frontrunning
description: MEV — frontrunning, sandwiching, backrunning, slippage, deadline, and transaction-ordering dependencies
---

# MEV, Frontrunning, and Transaction Ordering

The mempool is adversarial. Any transaction whose profitability depends on a price the attacker can move around it is exposed.

## Where to look

- **No slippage bound.** `swap(amountIn)` with no `amountOutMin`, or `minOut = 0`. A searcher sandwiches the user and captures the difference. Every user-initiated swap, deposit, and liquidation needs a bound.
- **No deadline.** A transaction with no `deadline` can be held by a builder and executed at a much worse price later.
- **Liquidation races.** A liquidator's call is front-run by a better-priced one, or the target self-liquidates first; the loser's transaction reverts. Check whether the design assumes a specific liquidator and whether the revert loses funds.
- **First-come claims.** A claim/redeem that is `msg.sender`-agnostic can be front-run by anyone (e.g. a signature-less claim to an address derived from calldata).
- **Backrunning the state change.** A state change (a price update, a reward accrual) that creates a temporary arbitrage is backrun before honest users react.
- **`block.timestamp` / `block.number` as a source of randomness or fairness.** Miner/validator-influenceable; commit-reveal without a binding is not secure.
- **Predictable addresses / CREATE2.** A deterministic address that can be pre-seeded before the intended deploy.
- **Approval race.** A `transferFrom`-based flow where an approval can be front-run by the spender (the classic ERC-20 allowance race; relevant if the protocol re-uses allowances).

## Attack plan

1. List user-facing value-moving calls and whether they carry `amountOutMin`/`minAmount`/`deadline`.
2. For each, simulate the sandwich: move the price before, execute the victim with their current bounds (or absence), move it back, capture the delta.
3. Check liquidations and claims for who can race whom.
4. Check any randomness for manipulability.

## Proof

For a missing slippage bound, show the sandwiched victim receiving far less than fair (or the searcher's profit). For a missing deadline, show execution at a stale price. A fork PoC is ideal.

## Fix

Require slippage bounds and deadlines on all user swaps/deposits; use TWAPs or private orderflow where appropriate; design liquidations with explicit incentives and no assumption about the caller; use commit-reveal or a VRF for randomness.
