---
name: cairo-felt-and-math
description: Cairo/Starknet felt252 math — field wrap, modular division, u256/u128/i128 and TryInto casts, fixed-point scaling, unsafe felt252 hash/amount trust
---

# Cairo felt252 and Math

`felt252` is a field element modulo the STARK prime `P = 2^251 + 17 * 2^192 + 1`, not a 256-bit integer. Its `+ - *` wrap in the field with no panic, its `/` is multiplication by the modular inverse, and casting between `felt252` and the bounded integers is the richest source of Cairo bugs.

Cairo has no floating point and no native fixed point, so every place a real-world quantity becomes a `felt252` or an integer is a place value can be created or destroyed — and repeated.

## Where to look

- **`felt252` `+ - *` never overflow — they wrap modulo `P`.** No panic, no checked build. Any supply, balance, counter, or timestamp kept in `felt252` can silently wrap. Look for `felt252` used as money (`balances: LegacyMap<ContractAddress, felt252>`) or as an accumulator.
- **`felt252` subtraction wraps to a huge field element.** `a - b` with `b > a` yields `P - (b - a)`, not an error and not `0`. A "balance decreases by more than it holds" bug is invisible at the type level.
- **`felt252` `/` is field division, not integer division.** `let x: felt252 = 5 / 2;` is a field element, not `2`. Any rate, fee, ratio, or share computed with `/` over `felt252` is wrong unless the denominator is invertible and the result is genuinely a field value (signatures, commitments, polynomial eval). Value-like `/` on `felt252` is a bug.
- **`felt252` `%` / `Rem` operate in the field.** Confirm intent before trusting either operand; a felt remainder is not an integer remainder.
- **`u128`, `u256`, `i128` are the arithmetic value types.** Keep money here; conversion is explicit and fallible.
- **`u256` is `{ low: u128, high: u128 }`.** Its `Div`/`Rem` route through `u256_safe_divmod`, which **panics on divide-by-zero**; `u256_overflowing_add`/`_sub`/`_mul` return an overflow flag you must check.
- **`TryInto` casts are fallible.** `felt.try_into().unwrap()` to `u128` panics when the value is `>= 2^128`; `u256.try_into()` to `felt252` panics at `>= P`. An `.unwrap()`/`.expect()` on attacker input is a DoS; a `unwrap_or_default()` that silently yields `0` is worse — it can zero a guard or a balance.
- **Widening vs narrowing.** `Into` is used for safe widening (e.g. `u128 -> u256`); `TryInto` for narrowing. A call that should be `try_into().expect("overflow")` but is `into()` hides the check.
- **`i128` sign encoding.** A "negative" felt is `P - x`; there is no two's-complement. Check the sign convention before any `felt252`-to-`i128` conversion and before subtracting two signed values.
- **Helper surface.** `core::integer::{u256_safe_divmod, u256_wide_mul, u256_overflowing_add, u256_overflowing_sub, u256_sqrt, u512}` and the `starknet::Math` / `core::math` / OZ `openzeppelin::utils::math` helpers. Hand-rolled versions that skip a bound are findings.
- **`pow` / exponentiation.** Integer `pow` grows fast; an unchecked `u128` power or a felt power overflows/wraps. Verify the exponent is bounded.
- **Fixed point and scaling.** WAD/RAY-style scaling (`10**18`) is manual. A missing or doubled scale factor moves value by `1e18`. Enumerate every scale constant and where it is applied.
- **Scale mixing.** Token A at 6 decimals, token B at 18, an oracle at 8. A missing `* 10**(18 - decimals)` between them silently misprices by `1e12`.
- **Round direction.** For each division, decide whether it should round toward the protocol (fees, shares minted, collateral) and confirm it does. A user-favorable direction is a slow leak.
- **Accumulators.** `reward_per_share`-style `felt252`/integer accumulators lose precision per update and can wrap over long horizons; check the update frequency and the running sum.
- **Unsafe `felt252` as a hash.** A `pedersen`/`poseidon` output truncated into `felt252`, or treated as a unique id, can collide; never use a felt hash as a balance or identifier.
- **Unsafe `felt252` as an amount / address.** A `ContractAddress` reinterpreted as a number, or a felt compared against an address, loses the address's structure.

## Attack plan

1. Inventory every `felt252`, `u128`, `u256`, and `i128` that touches value, supply, or authorization.
2. For each `felt252` op, decide field-vs-integer intent; if it is value math, it belongs in `u*`/`i*`.
3. For each cast, drive the boundary: can attacker input push `.unwrap()` past the target type's max, or trigger the silent `0` fallback?
4. For each division, compute the field result vs the intended integer result and the rounding direction.
5. Attempt a wrap: raise a `felt252` total above `P`, push an `i128` below its minimum, or overflow an unchecked `u128` multiply.
6. Check scale: compare each `10**n` constant against the decimals of every token and oracle it combines with.

## Proof

Use `snforge test` to demonstrate the concrete failure. For a cast DoS, call the entry with the boundary value and show the panic. For field division, assert the on-chain result differs from the intended integer quotient and show the value that moved. For a wrap, print the pre- and post-state and the attacker gain. Keep a candidate as a **lead** until the trace is reachable from an unprivileged caller; a High/Critical needs the working PoC or a complete trace.

## Fix

Keep money in `u128`/`u256`/`i128`; reserve field arithmetic for cryptography. Replace `felt252` `/` with integer `u256_safe_divmod`, guarding the zero divisor. Use `try_into()` with an explicit error branch instead of `.unwrap()`. Round monetary math in the protocol's favor and document every scale constant.

## Variants and adjacent bugs

- **Unsigned wrap in `u128`/`u256`** — an unchecked `*` or `+` past the type max; `u256_overflowing_mul` returns a flag you must check.
- **Field division disguised as integer division** — a rate or share computed with `/` over `felt252`.
- **Silent cast to zero** — `unwrap_or_default()`/`unwrap_or(0)` turning a too-large value into `0`.
- **Scale mismatch** — token `6` decimals combined with an oracle at `8` or `18` without conversion.
- **Accumulator drift** — repeated `reward_per_share` updates that lose precision or wrap.

## Do not flag

- Legitimate field arithmetic in signatures, commitments, and hashes (e.g. `pedersen`/`poseidon` inverses).
- Documented WAD/RAY scaling that is correct and consistently applied.
- Bounded, checked integer math with an explicit overflow branch.

## Leads vs findings

- A cast or division that *looks* wrong is a **lead**.
- A finding needs the reachable path plus a concrete value change (or panic) shown by `snforge`.
- Severity is one of **Critical, High, Medium, Low, Informational**, calibrated to value at risk and reachability.

## Related skills

- `ecosystems/cairo` — Cairo/Starknet platform model and idioms.
- `tooling/cairo-scarb` — Scarb and `snforge` build/test commands.
- `vulnerabilities/precision-rounding` — rounding and precision across ecosystems.
