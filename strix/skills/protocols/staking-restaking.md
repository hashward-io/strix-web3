---
name: staking-restaking
description: Staking and restaking — reward accrual, delegation accounting, slashing, unbonding, and points/incentive systems
---

# Staking and Restaking

Staking protocols track delegated balances and accrue rewards over time. The bugs are in the accounting of both across epochs, and in slashing.

## Where to look

- **Reward accrual math.** `rewardPerShare`/`accRewardPerShare` accumulators updated on every stake/withdraw/claim; a `dt * rate / totalStaked` that drifts or can be gamed by staking right before a reward and unstaking after (reward sniping — needs a time-weight or a checkpoint).
- **Delegation accounting.** Operator has `totalDelegated == Σ delegatorBalances`; a delegate/undelegate that updates one side but not the total; slashing that reduces the total but not each delegator (or vice versa).
- **Slashing.** Who can slash, how much, and how the loss is distributed; a slash that can make `totalDelegated < 0` or socialize incorrectly; slashing during unbonding (the exiting stake escapes the slash).
- **Unbonding / cooldown.** A cooldown that can be bypassed; an unbonding queue with a wrong entry; a withdrawal that pays out before the cooldown ends.
- **Epoch boundaries.** Reward/settlement computed at an epoch boundary that can be crossed mid-transaction; a stake in the same tx as a reward claim.
- **Restaking (EigenLayer-style).** Delegation to operators, share accounting across strategies, slashing conditions, and the withdrawal delay enforced on-chain vs off-chain. A restaked share valued per-strategy; a strategy that can be added with a manipulable exchange rate.
- **Points / incentives.** Off-chain points driven by on-chain balances — flag if a flash loan or round-trip inflates points.
- **Token and NFT staking.** `stake`/`unstake` reward math (see `protocols/vaults-erc4626`), double-claim, staking an NFT that is also used elsewhere.
- **Interest/fee-on-stake.** A fee taken on stake that also accrues rewards.

## Attack plan

1. Write the delegated-balance identity and the reward-accrual formula.
2. Find the function that updates one side of an identity and not the other.
3. Test reward sniping: stake immediately before an accrual, claim, unstake.
4. Test slashing: exit before a slash, or a slash that underflows/oversocializes.
5. Test the unbonding/cooldown bypass.

## Proof

A Foundry PoC: a stake/claim/unstake round-trip that extracts more rewards than the held time warrants; or a slash that leaves the accounting broken; or an unbonding bypass. Quantify.

## Fix

Use time-weighted or checkpointed reward accounting; update aggregate and per-user state atomically; distribute slashing pro-rata with an underflow guard; enforce cooldowns on-chain; rate-limit incentive systems.
