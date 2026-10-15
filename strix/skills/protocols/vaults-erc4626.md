---
name: vaults-erc4626
description: Vault and ERC-4626 review — strategies, share accounting, deposit/withdraw limits, fees, and allocation
---

# Vaults and ERC-4626

A vault takes assets, mints shares, and delegates the assets to a strategy. Bugs live in the share/asset ratio and in the strategy boundary.

## Where to look

- **Share inflation and donation.** See `vulnerabilities/erc4626-inflation`. Confirm the vault uses internal accounting or virtual offsets, not raw `balanceOf`.
- **`totalAssets()` composition.** Does it include assets in flight (being deposited into a strategy), locked, or pending withdrawal? A `totalAssets()` that omits a part lets shares be minted too cheaply.
- **Strategy trust and loss.** A strategy that can report a loss (reporting `totalAssets` down) socializes it across shareholders; check that the loss accounting cannot be front-run or timed.
- **Rounding.** `convertToShares`/`convertToAssets` and the `preview*` functions must round in the vault's favor and agree with the actual operations.
- **Fees.** Management/performance fee taken from `totalAssets` or minted as shares; a fee that is taken from the wrong base; a `harvest` that calls into a strategy and can be sandwiched.
- **Deposit/withdraw limits.** `maxDeposit`/`maxMint`/`maxWithdraw`/`maxRedeem` enforced? A limit bypassed by calling the underlying strategy directly or via a non-standard path.
- **Reentrancy / read-only reentrancy.** The vault's `totalAssets`/`convertToShares` is read by peers (lending markets, aggregators); if a callback during deposit/withdraw exposes a stale or manipulable value, those peers are exploitable.
- **Withdrawal queue / illiquidity.** A withdraw that depends on a strategy being liquid; a queue head that can be blocked; a "claim" that never pays.
- **Authorization.** Who can call `harvest`/`report`/`setStrategy`; can a strategy be swapped for a malicious one; can `emergencyWithdraw` be front-run.
- **ERC-4626 compliance.** `deposit` returning the correct shares; events; `asset()`; the standard's invariants.
- **Initialization.** `initialize()` front-run (see `vulnerabilities/upgradeability-proxy`).

## Attack plan

1. Determine the share/asset ratio source and test the inflation/donation attack.
2. Round-trip `deposit → withdraw` and `mint → redeem` for a profit or loss.
3. Test the fee computation and the `harvest` path.
4. Test deposit/withdraw limits.
5. If peers read the vault's price, test read-only reentrancy.

## Proof

A Foundry PoC showing: victim deposits and receives `0`/too-few shares; or a round-trip profit; or a peer protocol reading a manipulated `previewRedeem`. Quantify.

## Fix

Virtual shares/assets or internal accounting; consistent rounding; enforce `max*`; align `preview*` with actual math; reentrancy-guard the price getters peers consume; make the strategy boundary trustless or timelocked.
