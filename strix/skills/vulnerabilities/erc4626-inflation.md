---
name: erc4626-inflation
description: ERC-4626 and share-based vault issues — first-depositor inflation, donation, rounding, empty-vault division, and redeem asymmetry
---

# ERC-4626 and Share Inflation

Vaults convert between assets and shares with a ratio that any deposit can move. The attacks are about the order of operations around that ratio.

## Where to look

- **First-depositor inflation / donation attack.** An attacker deposits `1 wei`, then donates a large amount directly to the vault (`transfer` to `address(this)`), inflating `totalAssets` without minting shares. The next depositor's `assets * totalSupply / totalAssets` rounds **down to zero** shares; the attacker redeems for the victim's assets. Requires that the vault price off `balanceOf(address(this))` (or an `totalAssets()` that does) and that there is no minimum-liquidity lock.
- **`totalAssets()` from raw balance.** If `totalAssets()` is `asset.balanceOf(address(this))`, any direct transfer (donation) or fee-on-transfer changes the price mid-operation.
- **Empty-vault division.** `convertToShares(assets)` with `totalSupply == 0` — OpenZeppelin's `mulDiv` returns `0`, so the first depositor may get `0` shares; or a custom `assets * totalSupply / totalAssets` divides by zero. Check the `totalSupply == 0` branch.
- **Rounding asymmetry.** `previewDeposit` and `previewMint` (and `previewWithdraw`/`previewRedeem`) must round consistently and in the vault's favor; if they disagree with the actual `deposit`/`withdraw`, a user can mint/redeem for a profit around the boundary.
- **`preview*` vs actual mismatch.** Integration contracts (lending, aggregators) use `previewRedeem`/`previewMint` to value positions; if the actual operation differs from the preview, those integrators are exploitable (see read-only reentrancy).
- **`maxDeposit`/`maxWithdraw` ignored.** Public entry points that skip `max*` limits.
- **Share transfer hooks.** ERC-4626 with transferable shares plus an override that does not account for transfers (reward accounting breaks).
- **Inflation of `totalSupply` via direct share transfers** in protocols that read `balanceOf` for accounting.
- **Fee-on-deposit vs fee-on-withdraw asymmetry** creating a round-trip profit.

## Attack plan

1. Determine how `totalAssets()`/share price is computed. If it reads the raw balance or is donation-sensitive, the inflation attack is live unless `MINIMUM_LIQUIDITY`-style protection exists.
2. Compute the first-depositor attack with concrete numbers (attacker deposit, donation, victim deposit, victim shares, attacker redemption).
3. Check the `totalSupply == 0` path for division-by-zero or zero-share mint.
4. Verify `preview*` matches the actual math.

## Proof

A Foundry PoC that: attacker deposits `1`, donates `X`, victim deposits `Y`, victim receives `0` shares, attacker redeems for more than `1 + X`. Or the round-trip variant.

## Fix

Virtual shares/assets offset (`_decimalsOffset`, OpenZeppelin's mitigation); use internal accounting instead of `balanceOf`; seed `MINIMUM_LIQUIDITY` and burn it; round previews consistently; guard the empty-vault case.
