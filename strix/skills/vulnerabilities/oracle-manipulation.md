---
name: oracle-manipulation
description: Oracle and price-feed manipulation — spot vs TWAP, staleness, decimals, deviation, single-source and misconfigured feeds
---

# Oracle Manipulation

Any value derived from an oracle is an attack surface. The question is always: **who controls the price, for how long, and at what cost?**

## Spot vs manipulation-resistant

- **Spot price from an AMM** (`getReserves`, `balanceOf(pair)`, `slot0` as a raw price) is manipulable inside a single transaction with a flash loan. If the protocol reads a spot price and acts on it (mint, borrow, liquidate, settle), the attack is usually a Critical.
- **TWAP** resists single-block manipulation but is manipulable across many blocks and is stale in fast markets; check the window length, whether it can be moved with sustained capital, and whether it is read at the wrong moment.
- **Chainlink / PUSH oracles** — check `latestRoundData` usage: stale rounds ignored? `answeredInRound >= roundId`? a `minAnswer`/`maxAnswer` clamp that hides a real crash? a zero/negative answer accepted? a heartbeat that the consumer does not verify?

## Where to look

- Every function that uses a price, exchange rate, or ratio to move value.
- Decimal handling: feed decimals vs token decimals vs protocol fixed-point. A missing scale conversion is often a theft path.
- Rounding direction of the price used to mint (down) vs burn/borrow (up).
- **Single-source dependency** — one feed, one pool, no fallback; a failure or manipulation zeroes the protocol.
- **Derived/oracle-of-oracle** — an LP-token or receipt-token price that is itself AMM-derived becomes spot-manipulable.
- **`previewX`/view getters** that peers read (read-only reentrancy via a manipulated price).

## Proof

Show the manipulation transaction: flash-borrow → move the price → call the vulnerable function → profit → repay, with concrete numbers. For stale-feed bugs, show the stale state being consumed.

## Fix

Use a manipulation-resistant oracle (TWAP of adequate window, Chainlink with full validation), validate staleness/bounds/decimals, add circuit breakers, and never derive a price from a single spot pool.
