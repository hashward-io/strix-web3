---
name: oracles
description: Oracle review — Chainlink/PUSH feeds, TWAPs, staleness, deviation, decimals, fallbacks, and consumer validation
---

# Oracles

An oracle is a trust boundary the protocol reads as truth. The bug is usually in the **consumer** not validating the feed, not in the feed itself.

## Feed types

- **Chainlink aggregator.** `latestRoundData()` returns `(roundId, answer, startedAt, updatedAt, answeredInRound)`. Validate: `answer > 0` (or handle negative for signed feeds), `updatedAt != 0`, `updatedAt` within a heartbeat, `answeredInRound >= roundId`, and a sane min/max. A `minAnswer`/`maxAnswer` circuit breaker can hide a real crash (the feed reports the bound, not the price).
- **Sequencer feeds (L2).** On Arbitrum/Optimism, check `latestRoundData` **and** the sequencer uptime feed (`sequencerUptimeFeed.latestRoundData()`, `startedAt`, grace period). Missing this means stale prices during an outage.
- **TWAP.** Uniswap V2/V3 `consult`/`observe` over a chosen window; check the window length, the cardinality (enough observations), and whether the window can be moved with sustained capital.
- **Spot from a pool.** Manipulable (see `vulnerabilities/oracle-manipulation`).
- **Custom / signed price.** A set of signers and a threshold; a signature with no nonce/deadline/chainId (see `vulnerabilities/signature-replay`).
- **LP / receipt token oracles.** A price derived from another protocol's derived value — compounding manipulability.

## Where to look

- Every call to a price/rate getter and whether the return is validated.
- **Decimals.** Feed decimals vs token decimals vs protocol fixed-point; a missing scale conversion; a hard-coded `1e8`/`1e18`.
- **Staleness.** A heartbeat constant vs the actual feed; a `require` on `updatedAt` that is missing.
- **Fallback / multi-source.** A primary and a fallback, and the switch logic (a fallback that is worse, or a switch that can be forced).
- **Zero/invalid answer.** `answer == 0` accepted, leading to a division by zero or a free mint/borrow.
- **Signed/int negative answer.** For a feed that can go negative (some index feeds), a `uint` cast truncates.
- **Read-only reentrancy.** A price getter that peers read mid-callback (see `protocols/amm-dex`, `protocols/vaults-erc4626`).
- **Price when paused / market closed.** A stale weekend/holiday price for a real-world asset.

## Attack plan

1. List every price read and the feed behind it.
2. For each, check the full validation set above.
3. Attack the manipulation window (spot or short TWAP).
4. Attack decimals/scale.
5. Check the L2 sequencer path if applicable.

## Proof

For a missing validation, show the consumption of a stale/zero/bound price and the impact (free borrow, wrong liquidation). For manipulation, the flash-loan sequence. A fork PoC is ideal.

## Fix

Validate every field of `latestRoundData`; check the L2 sequencer feed with a grace period; normalize decimals explicitly; use a TWAP window long enough to resist sustained capital; add fallbacks and circuit breakers; never read a single spot pool as truth.
