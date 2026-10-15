---
name: dos-griefing
description: Denial of service and griefing — reverting loops, gas limits, unbounded arrays, forced ETH, and stuck funds
---

# Denial of Service and Griefing

A cheaper attack that stops the protocol for everyone is still a finding. Ask who can make a shared function revert, and at what cost.

## Where to look

- **Unbounded loops.** Iterating over an array of users, proposals, orders, or tokens that grows without bound. Eventually the gas exceeds the block limit and the function reverts permanently. Look for `for` over a storage array where the array is user-growable.
- **Reverting transfer in a loop.** A batch `withdraw`/`claim` that iterates recipients with `transfer`/`call` and reverts if one reverts — one bad or blacklisted recipient blocks the batch (and if the batch is mandatory, the whole protocol).
- **Push vs pull payments.** Sending ETH/tokens to many addresses in one call; a single reverting recipient (contract without `receive`, blacklisted address) blocks it. Prefer pull.
- **`transfer`/`send` gas stipend.** `transfer` forwards 2300 gas; a recipient with a `receive` that writes storage reverts, blocking a payout.
- **Forced ETH / forced balance.** `address(this).balance` used as an accounting source can be inflated via `selfdestruct` (pre-Cancun) or block reward, breaking `==` checks; a contract that rejects incoming ETH can be forced to hold it.
- **Revert-on-empty / zero-amount.** A function that reverts when an amount is zero can be griefed if an attacker can drive the amount to zero (see precision truncation).
- **Flash-loan / dust griefing.** An attacker who must only pay gas to make a state invalid.
- **`require` on external state.** A check that depends on an external contract that can be made to revert (an oracle that can be paused, a token that can be blacklisted).
- **Queue head-of-line blocking.** A pending-item queue where the head item can be made unprocessable.
- **Storage/refund griefing.** Filling storage so operations hit the gas limit.

## Attack plan

1. Find every loop over a user-growable collection and compute where it breaks.
2. Find every push payment and whether one recipient can block the batch.
3. Find every accounting read of `address(this).balance` and whether it can be forced.
4. For each `require`, ask who controls the checked value and whether they can make it fail cheaply.

## Proof

Show the state from which the shared function reverts forever (or for a bounded time) and the cost to the attacker. A Foundry PoC with a reverting receiver or a filled array is ideal.

## Fix

Bound loops and paginate; pull-payment patterns; skip/try-catch failing recipients with a claim fallback; never derive accounting from `address(this).balance`; allow zero amounts; make griefing costs exceed the damage.
