---
name: solana-arithmetic-and-casts
description: Solana Rust arithmetic - checked vs wrapping/overflow, as-cast truncation, u64/u128/i64 conversion, lamport and decimal scaling, rounding direction, div-by-zero, unwrap panics
---

# Arithmetic, Casts & Panics (Solana)

Rust's default overflow behavior flips between debug and release, `as` casts silently truncate,
and a single `unwrap()` on attacker data is a denial of service. Every one of these is on-chain
state the attacker can reach by choosing instruction arguments.

## Where to look

- **`checked_*` vs wrapping/overflow** — `u64::checked_add/checked_sub/checked_mul/checked_div/
  checked_rem` return `Option`; `wrapping_*` deliberately wraps; `saturating_*` clamps; plain
  `a + b`, `a * b`, `a - b` **panic on overflow in debug** and **wrap in release** unless
  `overflow-checks = true`. An auditor must know which profile ships: Cargo release defaults to
  `overflow-checks = false`; Anchor's generated `Cargo.toml` may set it true. Either way, a
  release wrap is a silent accounting bug.
- **`as` casts** — `x as u32`, `x as u8`, `x as i64` truncate the high bits and reinterpret sign:
  `(u64) as u32` drops everything above 2^32-1; `(i64) -1 as u64` is `u64::MAX`; `(u128) as u64`
  truncates. Watermark/`TryFrom`:
  `u32::try_from(x).map_err(|_| ErrorCode::Overflow)?`.
- **`u64`/`u128`/`i64` conversions** — lamports and token amounts are `u64`; intermediate share
  math often needs `u128` to avoid overflow, then a checked narrowing back. `i64` appears in
  timestamps (`Clock.unix_timestamp`) and oracle prices (`Pyth` `expo` is `i32`).
- **Decimals / lamports scaling** — `LAMPORTS_PER_SOL = 1_000_000_000`; token scaling is
  `10u64.pow(decimals)`. Mixing a 6-decimal mint with a 9-decimal one, or lamports with token
  base units, is a scale bug. `spl_token::amount_to_ui_amount` / `ui_amount_to_amount` show the
  intended conversion.
- **Rounding direction** — `checked_div` truncates toward zero. In share math, division must
  round *against* the user for deposits/withdrawals; deriving `shares = amount * total / supply`
  (round down) vs `amount = shares * total / supply` (round down) changes who gets the dust.
  Multiply before dividing to preserve precision.
- **Division by zero / modulo by zero** — `checked_div(0)` returns `None`; plain `/ 0` panics. A
  zero denominator from empty-supply state (`total_shares == 0`) is reachable.
- **`unwrap()` / `expect()` as DoS** — `try_borrow_data().unwrap()`, `.checked_sub(..).unwrap()`,
  `.parse().unwrap()`, `Pubkey::from_str(..).unwrap()`. Any of these panicking aborts the whole
  transaction; if it aborts a legitimate flow (a withdrawal, a crank, a liquidation) it is a
  griefing vector even without theft.
- **Comparison/logic errors** — off-by-one in ranges, `<=` vs `<`, sentinel `0`/`u64::MAX`
  handling, and `as` on an enum discriminant read from account data.

## Attack plan

1. Determine the shipped build profile (release `overflow-checks`) and re-evaluate every naked
   `+ - *`.
2. Find every `as` cast on a value that can exceed the target width or be negative.
3. Locate scale constants (`decimals`, `LAMPORTS_PER_SOL`) and confirm both sides use the same.
4. For each division, decide the correct rounding direction and whether zero is reachable.
5. Grep `.unwrap()`/`.expect()`/`panic!`/array indexing in instruction handlers.

## Proof

- Unit test the panic/overflow directly:

```rust
#[test]
fn cast_truncates() {
    let big: u128 = u64::MAX as u128 + 1;
    assert_eq!(big as u64, 0); // silent truncation
}
```

- Anchor: `anchor test` sending the boundary argument (`u64::MAX`) and showing wrap (release) or
  a panic that blocks a legitimate path. In LiteSVM/`solana-program-test`, submit an amount that
  makes `total_shares == 0` and observe the abort. A captured panic message or a wrapped balance
  delta is the evidence.

## Fix

Use `checked_*`/`saturating_*` and propagate errors; use `TryFrom`/`try_into` instead of `as`;
keep a single canonical unit and convert once; multiply before dividing and pick the
protocol-favoring rounding; reject zero denominators; replace `unwrap()` with `?` and typed
`ErrorCode`s. See `hacking_agents/math-precision`, `ecosystems/solana`.
