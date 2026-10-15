---
name: amm-dex
description: AMM and DEX review — constant-product and concentrated liquidity, fee accounting, slippage, LP tokens, and MEV
---

# AMM / DEX

Automated market makers concentrate almost every Web3 bug class at once: math, oracles, tokens, MEV, and accounting. Assume the attacker can move the price within a transaction.

## Domains

- **Constant-product (`x*y=k`).** `getAmountOut` formula correctness (the `997/1000` fee math), fee-on-transfer tokens, `k` invariant preservation across add/remove liquidity, minimum liquidity lock, first-LP share pricing.
- **Concentrated liquidity (Uniswap V3/V4).** Tick math, `sqrtPriceX96` overflow, liquidity delta sign, fee growth accounting (`feeGrowthGlobal - feeGrowthOutside`), position boundary conditions, flash accounting in V4 (transient balances), hook trust.
- **Curve-style stableswap.** Amplification (`A`) update, `D` (invariant) Newton-solver convergence and its rounding, imbalance fees, `get_virtual_price` manipulation (a classic read-only reentrancy source).
- **Balancer-style weighted pools.** Weight/exponent math, `pow` rounding, join/exit formulas.

## Where to look

- **Fee accounting.** Fees credited to LPs vs to a protocol treasury; a `feeGrowth` accumulator updated on swap but not on liquidity change; rounding of fees.
- **LP token value.** `totalSupply == 0` first-mint pricing; a donation that moves `reserves` but not `totalSupply`; the pool's own `balanceOf` used as a reserve source.
- **Price as an oracle.** Any protocol reading the pool's spot price (see `vulnerabilities/oracle-manipulation`).
- **Slippage and deadlines.** Missing `amountOutMin`/`deadline` (see `vulnerabilities/mev-frontrunning`).
- **Token decimals.** Pools assuming equal decimals; a `1e18` constant.
- **Add/remove liquidity asymmetry.** A rounding direction that lets a provider withdraw more than they added.
- **Reverted swap partial state.** A swap that updates reserves before a token transfer that can re-enter (see reentrancy).

## Attack plan

1. Identify the AMM model and read the core invariant math.
2. Test the round-trip: `addLiquidity → swap → removeLiquidity` and `swap → swap` for a profit or stuck funds.
3. Test the first-LP path and the `totalSupply == 0` branch.
4. Test fee-on-transfer / rebasing tokens through the math.
5. Check every external read of the pool price.

## Proof

A Foundry PoC with a fork of the target pool (or a mock) showing the profit or the invariant break, with concrete numbers. For math, a fuzz test that finds a violating input.

## Fix

Correct the fee/invariant math; use internal reserves rather than `balanceOf`; lock first-liquidity; require slippage bounds and deadlines; expose a manipulation-resistant TWAP for external consumers; handle token decimals and fee-on-transfer explicitly.
