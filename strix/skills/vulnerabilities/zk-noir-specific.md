---
name: zk-noir-specific
description: Noir-specific issues — unconstrained functions, Field overflow, u8/u32/u64 range checks, arrays and Global len, brillig hints, nargo test vs proof, verify_proof
---

# Noir-Specific Circuit Bugs

Noir hides a lot of constraint plumbing, which makes the remaining footguns sharp: `unconstrained` hints, silently wrapping `Field`, integer casts, and the gap between `nargo test` passing and a proof actually binding the statement.

## Where to look

- **`unconstrained fn`.** An `unconstrained` function computes a hint whose result is **not** constrained. If its output flows into the proof without a later constraint, a malicious prover substitutes any value.
- **Oracles and foreign calls.** `#[oracle]`/brillig foreign calls (`std::oracle::*`, `println`, environment reads) are unconstrained; every result must be re-checked in constrained code (`assert_eq!(hint(x), expected)`).
- **`Field` overflow.** Noir `Field` wraps modulo the proving field (the BN254 scalar field by default). `+ - *` on `Field` never panic and wrap silently; a "negative" is `p - x`. Any `Field` used as a counter, amount, or index can wrap. Constrain the range or use an integer type.
- **`u8` / `u32` / `u64` range checks.** Noir integers are range-checked, and plain `+ - *` are **checked** (overflow fails the proof) — but `WrappingAdd`/`WrappingSub`/`WrappingMul` opt into wrap.
- **`as` casts truncate silently.** `x as u32` from a `u64` drops the high bits with no error. Check every cast and every `Wrapping*` use.
- **Mixed-width arithmetic.** Combining `Field` and `u*`, or a `u64` with a `u32`, can promote unexpectedly; verify the widths at each operation.
- **Arrays and `Global` length.** `[T; N]` has a compile-time length; `Global` constants parameterize `N`. A mismatched length, an index not range-checked, or a read past a fixed bound is a bug.
- **Dynamic collections.** `Vec` lives in unconstrained code only; if its length reaches the proof it must be constrained, or a prover pads/truncates it.
- **`brillig` hints.** `#[brillig]`/unconstrained Brillig executes off-circuit; correctness must be enforced by constraints on the returned values. Treat Brillig output as untrusted input.
- **`nargo test` vs proof.** `nargo test` runs the ACIR interpreter over your test inputs and does enforce constraints **for those inputs**, but it cannot prove the circuit is sound for all inputs — an under-constrained circuit often passes every test.
- **`verify_proof` and recursion.** `std::verify_proof` (and recursive verifiers) must receive the verification key and public inputs in the exact expected order and format; a mismatch binds the wrong statement.
- **`assert` misuse.** `assert`/`assert_eq` inside constrained code generates constraints, but inside `unconstrained fn` it does **not** — a check written in a hint guards nothing on-chain. Move security checks into constrained functions.
- **Test-only code paths.** `#[test]` helpers and debug prints that differ from the proven path, or a `comptime` branch that selects a different relation than production.

## Attack plan

1. List every `unconstrained fn`, `#[oracle]`, and brillig call; confirm each result is constrained before use.
2. Classify each arithmetic type: `Field` (wraps) vs `u*` (checked). Look for silent wrap and `as` truncation.
3. Check array lengths, `Global` bounds, and every index for a range constraint.
4. Verify `assert`/`assert_eq` checks live in constrained functions, not hints.
5. Inspect `verify_proof` call sites for vk/public-input order and binding.
6. Generate a witness with `nargo` and confirm the honest path proves; then attempt a forged witness.

## Proof

Use `nargo execute` to produce the witness and `nargo prove` + `nargo verify` (or `bb prove` + `bb verify`) to obtain verifier output. Demonstrate a **forged witness** for an `unconstrained`/`Field`-wrap hole, or a truncated cast that changes the value. A passing `nargo test` is not the proof — show the verifier accepting an out-of-spec witness or a value change.

## Fix

Constrain every `unconstrained`/oracle/brillig result before it influences the statement; keep security `assert`s in constrained code. Use `u8`/`u32`/`u64` with checked arithmetic and explicit range/`as`-cast bounds instead of `Field` for value math; avoid `Wrapping*` unless intended. Range-check array indices and pin lengths via `Global`. Bind vk and public inputs exactly in `verify_proof`. Add negative tests and prefer proof-based verification over `nargo test` alone.

## Variants and adjacent bugs

- **Unconstrained hint** — an `unconstrained fn`/oracle result left unbound.
- **`Field` wrap** — silent modular wrap in value math.
- **Truncating cast** — `as` dropping high bits.
- **Unchecked array index / length** — reading past a fixed bound.
- **Test-passes-but-unsound** — an under-constrained circuit `nargo test` cannot catch.

## Do not flag

- `unconstrained` results re-checked in constrained code with `assert_eq!`.
- Integer types with checked arithmetic and explicit range bounds.
- `assert`/`assert_eq` inside constrained functions.

## Leads vs findings

- An `unconstrained`/`Field` smell is a **lead**; the forged witness is the finding.
- Show `nargo prove`/`bb verify` accepting an out-of-spec witness or a value change.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/zk` — Noir and proving-system model.
- `tooling/zk-noir` — `nargo`/`bb` build, prove, and verify.
- `vulnerabilities/zk-underconstrained-circuit` — missing constraints.
