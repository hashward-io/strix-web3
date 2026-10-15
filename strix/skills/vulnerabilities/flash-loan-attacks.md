---
name: flash-loan-attacks
description: Flash-loan-amplified attacks — oracle/price manipulation, governance, collateral, and self-funding exploits
---

# Flash-Loan Attacks

Assume the attacker has unlimited capital for the duration of one transaction. Every assumption that "moving this value would be too expensive" is false.

## What flash liquidity enables

- **Oracle and price manipulation** — borrow a huge amount, move a spot price or a thin TWAP, hit the protocol, unwind, repay in the same tx. See `vulnerabilities/oracle-manipulation` and `vulnerabilities/price-manipulation`.
- **Governance takeover** — if voting power is `balanceOf`-based and snapshot-less, borrow voting tokens, pass a malicious proposal (or flip a quorum), then return them. Governance must snapshot at proposal creation (`getPastVotes`) to resist this.
- **Collateral inflation** — deposit a manipulable asset as collateral, borrow against the inflated price, default. Check whether collateral value can be moved within the same block as the borrow.
- **Self-funding self-liquidation** — manipulate your own position's health factor to trigger a profitable liquidation of it.
- **Reward sniping** — deposit right before a reward snapshot with borrowed funds, claim, withdraw.
- **AMM invariant / fee abuse** — exploit a pool's fee math or minting with a large single swap.
- **Front-run-to-trigger state** — the attacker doesn't need to profit directly from the manipulation; triggering a stale/liquidatable state is enough.

## Where to look

- Any value read from a source the attacker can move in the same transaction (spot reserves, `balanceOf`, `slot0`).
- Governance with `balanceOf`/`getVotes` read at vote time rather than `getPastVotes` at snapshot.
- Collateral or health computation that reads a live price.
- Reward/settlement windows with no minimum holding period.

## Attack plan

1. For every value-moving decision, ask: "can I change the inputs to this decision within one transaction and profit?"
2. Write the atomic sequence: `flashLoan → manipulate → exploit → unwind → repay`.
3. Include the loan fee in the math; the attack must be net-positive.

## Proof

A Foundry mainnet-fork test using a flash-loan provider (Aave/Balancer/Uniswap) that demonstrates net profit after fees is the strongest PoC. Otherwise, a concrete numeric trace.

## Fix

Use manipulation-resistant oracles; snapshot governance power at proposal creation; enforce a minimum holding period or time-weighted balances for rewards; cap per-block value movement.
