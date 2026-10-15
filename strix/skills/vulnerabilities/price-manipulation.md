---
name: price-manipulation
description: AMM price and balance manipulation — donation attacks, sandwiching, invariant abuse, and share-price distortion
---

# Price and Balance Manipulation

Distinct from oracle bugs: here the attacker manipulates an on-chain value the protocol reads (pool reserves, token balances, share totals) rather than a misconfigured feed.

## Common shapes

- **Donation attack** — inflate a contract's token balance directly (`transfer` to it) so a value computed from `balanceOf(address(this))` jumps. Classic in ERC-4626 vaults (see `vulnerabilities/erc4626-inflation`) and any contract that prices off its own balance rather than internal accounting.
- **AMM invariant abuse** — swap to skew `reserve0/reserve1`, then hit a function that reads reserves as a price (lending against an LP, minting against a pool).
- **First-depositor / rounding-to-zero** — the first depositor can set the share price so later depositors round to zero shares. Mitigated by `MINIMUM_LIQUIDITY`-style burns; flag only when it survives or compounds.
- **Sandwich / MEV** — user transactions with no slippage bound (`amountOutMin = 0`) can be sandwiched. See `vulnerabilities/mev-frontrunning`.
- **Self-referential accounting** — the protocol computes a price from its own internal ratio that the attacker can freely move through a normal entry point.

## Where to look

- `balanceOf(address(this))`, `token.balanceOf(pool)`, `reserve0/reserve1`, `slot0`, `getReserves`, `totalSupply`/`totalAssets` reads used in pricing, minting, liquidations, or fee math.
- Any function whose output depends on a ratio the attacker can change with a single transfer or swap.
- Absence of a slippage/deadline bound on value-moving calls.

## Proof

Concrete numbers: the pre-state, the manipulation (transfer/swap with amounts and costs), the distorted value, and the profit after unwinding. A Foundry PoC against a mainnet fork is ideal.

## Fix

Use internal accounting instead of raw balances; use TWAPs; enforce slippage and deadlines; seed `MINIMUM_LIQUIDITY`; require minimum output amounts.
