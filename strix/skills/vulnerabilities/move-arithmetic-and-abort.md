---
name: move-arithmetic-and-abort
description: Move integer arithmetic - overflow/underflow aborts, as-cast truncation, division and rounding, abort code leakage, assert! misuse, gas/abort-based DoS
---

# Arithmetic, Casts & Aborts (Move)

Move integers are bounded and **abort** on overflow/underflow/divide-by-zero rather than wrapping.
That prevents silent wrap, but an unguarded arithmetic abort is still a denial of service, and
`as` casts between integer widths truncate silently.

## Where to look

- **Overflow / underflow abort** — `a + b`, `a - b`, `a * b` on `u8`..`u256` abort
  (`EADD_OVERFLOW`, `ESUB_UNDERFLOW`, `EMUL_OVERFLOW` VM codes) when out of range. A subtraction
  `balance - amount` where `amount` can exceed `balance` aborts the whole transaction instead of
  failing cleanly; decide whether that blocks a legitimate path. Sui Move now has `u256`; other
  Move flavors stop at `u128`. Sui's `std::u64`/`std::u128`/`std::u256` wrap in
  *wrapping* helpers only if you call `wrapping_add` etc.; plain `+` aborts.
- **Unchecked `+`/`*` on user input** — a `total_supply + amount` or `price * quantity` with no
  bound aborts when the attacker supplies `u64::MAX`. Even though no wrap occurs, the abort is a
  griefing vector if it corrupts a shared object update or a crank.
- **Division / rounding** — `/` truncates toward zero; `%` is the remainder. Move has no
  `checked_div` returning `Option` — division by zero aborts. `x * a / b` must multiply before
  dividing to preserve precision; `(x / b) * a` loses precision. Shares/LP math must round in the
  protocol's favor. Watch `u128`/`u256` intermediate promotion.
- **`as` casts** — `(x as u64)` from a wider type truncates the high bits; `(x as u8)` keeps the
  low byte. There is **no** negative type in Move, so casts are width-only, but `u128 -> u64` and
  `u256 -> u128` still silently drop bits. Never cast untrusted widths down without a bound check.
- **`abort` codes leaking** — `abort ECODE` (and `assert!(cond, ECODE)`) reveals internal state via
  the code. Distinct codes for "price too low" vs "unauthorized" can be an oracle for probing; more
  importantly, `assert!` with a boolean only cannot express a rich error and is easy to misuse
  (`assert!(true, ...)`, or checking the wrong condition).
- **`assert!` misuse** — `assert!(cond, code)` aborts when `cond` is **false**. A subtly inverted
  condition (`assert!(amount > 0)` vs `assert!(amount == 0)`) or a guard placed after the state
  mutation it was meant to protect. Check ordering.
- **Gas / abort-based DoS** — unbounded loops over `vector` (`vector::length`,
  `vector::push_back`) with attacker-grown vectors exhaust gas and abort; a growing `Table`
  iteration is bounded only by gas. A single abort in a shared object's transaction can starve all
  users of that object (`sui` shared-object contention).

## Attack plan

1. Determine the max width per value (`u64`/`u128`/`u256`) and whether intermediates can overflow.
2. Find every subtraction that can go negative and every multiplication of two large inputs.
3. For each division, confirm the multiplication precedes it and the rounding direction is safe.
4. Grep `as` casts, especially down-casts on decoded/user values.
5. Check `assert!` conditions for inversion and ordering relative to state writes.
6. Look for loops whose trip count is attacker-controllable.

## Proof

- Sui: `sui move test` with `#[expected_failure(abort_code = <module>::<ECODE>)]` for the intended
  path, and a companion `#[test]` that shows the abort occurs on a legitimate call (DoS) or that a
  cast truncates:

```move
#[test]
fun cast_truncates() {
    let big: u128 = (1u128 << 64) + 7;
    assert!((big as u64) == 7); // silent truncation
}
```

- Aptos: `aptos move test` with `#[expected_failure(arithmetic_error, location = ...)]`.
- For DoS, show a shared/production object path that aborts at the boundary input.

## Fix

Bound inputs and use explicit comparisons before arithmetic; keep a single integer width and
promote (`u128`/`u256`) for intermediates; multiply before dividing and choose protocol-favoring
rounding; guard down-casts with `assert!(x <= MAX, EOVERFLOW)`; replace ambiguous `abort` codes
with typed `const E...`; return `Option`/`Result`-style errors where a clean failure is expected
rather than aborting. See `hacking_agents/math-precision`, `ecosystems/move`, `tooling/move-cli`.
