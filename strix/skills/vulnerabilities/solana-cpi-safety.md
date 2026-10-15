---
name: solana-cpi-safety
description: Solana CPI safety - arbitrary/unvalidated target program, CPI to attacker program, invoke_signed seed verification, CPI reentrancy, lamport manipulation around CPI
---

# CPI Safety (Solana)

A Cross-Program Invocation hands control to another program. Solana has **no EVM-style
reentrancy guard** and no `msg.sender`: the callee is only as trustworthy as the program id you
verified, and it can mutate any writable account you passed it while control is out.

## Where to look

- **Arbitrary program id in CPI** — the target program account is passed as `AccountInfo` /
  `UncheckedAccount` instead of `Program<'info, System>` / `Program<'info, Token>` /
  `Program<'info, Token2022>` (or `Interface<'info, TokenInterface>`). Anchor's `Program<T>`
  checks both `executable == true` and `key == T::id()`; a bare `AccountInfo` checks neither.
- **Unvalidated target program** — `#[account(address = ...)]` missing on the program account, or
  a stored `program_id` field read from account data. An attacker points the CPI at their own
  program, which returns `Ok` and does nothing, or at one that re-enters you.
- **CPI to attacker program** — often reached via a "callback"/"hook" style design or a
  user-supplied program for a plugin (e.g. a Token-2022 transfer hook). Treat any program you
  did not hard-code as hostile.
- **Missing `invoke_signed` seed verification** — `invoke_signed` signs for a PDA using whatever
  seeds you give it. If the seeds are attacker-influenced or not re-derived with
  `find_program_address`, the program lends its signature to an arbitrary account. Always assert
  the signed `(seeds, bump)` derive to `account.key()`.
- **Reentrancy via CPI** — Solana forbids a program calling *itself*, but A→B→A and A→B→C→A are
  legal. If your handler reads state, CPIs, then writes state, the callee (or a program it calls)
  can re-enter a *different* instruction of yours and observe stale state. Read-only reentrancy is
  real: a peer program reading your `total_assets` mid-CPI can be drained.
- **State written after CPI** — checks-effects-interactions is an Anchor-agnostic rule; do all
  account mutations via `try_borrow_mut` *before* the CPI, then re-load after.
- **Lamport / balance manipulation around CPI** — a writable account passed to a CPI can have its
  lamports moved by the callee; code that computes `account.lamports()` before the CPI and trusts
  it last is exploitable. `system_program::transfer` CPI with attacker-chosen from/to bypasses
  your in-program accounting.
- **`AccountInfo` mutation via `try_borrow_mut_lamports`** on a non-owned account panics; verify
  ownership assumptions match the CPI's account metas.

## Attack plan

1. Enumerate every CPI (`invoke`, `invoke_signed`, `CpiContext::new*`, `program.methods(...)`).
2. For each target, confirm the program id is hard-coded or constrained, and `executable`.
3. For each `invoke_signed`, re-derive the PDA and compare.
4. Order the handler: does any state get written after the CPI? Can a peer observe it mid-call?
5. Pass a malicious program in place of the expected one and observe the effect.

## Proof

- Anchor: `anchor test` with a mock program deployed by the test; pass its id where the real
  program is expected and show the instruction completes (used to prove arbitrary-CPI / no
  validation).
- LiteSVM lets you register both programs and submit the crafted transaction:

```rust
let mut svm = LiteSVM::new();
svm.add_program_from_file(program_id, "target/deploy/prog.so")?;
svm.add_program_from_file(evil_id, "target/deploy/evil.so")?; // returns Ok, does nothing
let res = svm.send_transaction(tx); // victim instruction accepts evil_id as target
```

For reentrancy, have the mock program call back into a second instruction of your program while
the first is mid-flight, and show the re-entered read sees the pre-CPI value.

## Fix

Type CPI targets as `Program<'info, T>` or `Interface<'info, TokenInterface>`; add
`#[account(address = expected::ID)]`. Validate `invoke_signed` seeds with `find_program_address`.
Follow checks-effects-interactions around every CPI and reload accounts after it. Guard
read-only consumers with a protocol-level state flag. See `vulnerabilities/reentrancy`,
`ecosystems/solana`, `tooling/solana-anchor`.
