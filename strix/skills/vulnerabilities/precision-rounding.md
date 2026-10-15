---
name: precision-rounding
description: Fixed-point and integer precision — rounding direction, truncation, decimals/scale mixing, division-before-multiply, unchecked casts
---

# Precision and Rounding

Solidity has no floats. Every division truncates. Every place where the protocol turns a real-world value into an integer is a place where a satoshi can be created or destroyed — and repeated.

## Where to look

- **Rounding direction.** For each division, ask which way it rounds and who benefits. Fees and shares-to-mint should round **against** the user (protocol-favorable); assets-out and collateral-value should round **against** the user too. A direction that favors the user is a slow leak.
- **Division before multiplication.** `a / b * c` loses precision that `a * c / b` keeps. In reward math and ratio math this is a real bug class, not a style nit.
- **Truncation to zero.** A `shares = assets * totalSupply / totalAssets` where `totalAssets > assets * totalSupply` yields `0` — free deposits or lost funds. Check every division where the numerator can be the smaller operand.
- **Decimals and scale mixing.** Token A has 6 decimals, token B has 18; the oracle has 8. A missing `* 10**(18 - decimals)` or a `1e18` hard-coded against a 6-decimal token shifts value by `1e12`. Enumerate every decimal used and confirm the conversion exists.
- **Unchecked / down-casts.** `uint128(x)`, `int256(uint256(x))`, `uint64` counters, `int8` in packed structs — a value that overflows the cast silently wraps or truncates. Check `SafeCast` usage.
- **Overflow around `unchecked`.** A deliberately `unchecked` block that hides a real overflow (e.g. `unchecked { total -= amount; }` where `amount > total` underflows to a huge number).
- **Signed/unsigned footguns.** `int256` division truncates toward zero; negative rounding and `abs()` of `type(int256).min` overflow.
- **Accumulator drift.** `rewardPerShare`-style accumulators (`acc += rate * dt * 1e18 / totalStaked`) lose precision per update when `dt` is small; over many updates the sum drifts from `rate * totalTime`.

## Attack plan

1. List every division, cast, and decimal constant in the in-scope math.
2. For each, compute the worst-case rounding error and whether it is repeatable.
3. Look for a round-trip (deposit then withdraw, stake then unstake, borrow then repay) that returns more than it took, or repeatedly leaves dust.
4. Check the accumulator loops for drift.

## Proof

Concrete numbers: the inputs, the truncated value versus the exact value, and the profit or loss after one call and after N calls. A Foundry fuzz test that finds a round-trip gain is ideal.

## Fix

Multiply before dividing; round consistently in the protocol's favor; use `Math.mulDiv` for full-precision intermediate math; normalize decimals explicitly; use `SafeCast`; document where rounding is intentional and by how much it can drift.
