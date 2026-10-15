---
name: solana
description: Solana program playbook — Anchor, native, Pinocchio; account model, PDAs, CPIs, Token-2022, compute budget, and the Solana bug-class map
---

# Solana Ecosystem

Solana programs are stateless code that operate on **accounts passed in explicitly**. There is no state inside the program; all state lives in accounts, and the runtime does not verify that the accounts you received are the ones you intended. That single fact drives most Solana bugs.

## When to use

- An Anchor, native (`solana_program`), or Pinocchio Rust program; a deployable `.so`; an `Anchor.toml`.
- Token / Token-2022 integration, PDAs, or CPI-heavy code.
- You need the bug-class map before narrowing to `vulnerabilities/solana-cpi-safety` or `tooling/solana-anchor`.

## Program models

- **Anchor (`#[program]`, `#[derive(Accounts)]`):** constraints (`#[account(mut)]`, `seeds`, `bump`, `has_one`, `owner`, `token::mint`, `constraint`) do most checks — audit the constraints, not just the handler.
- **Native (`solana_program`):** manual `next_account_info`, `ProgramError::*`. Every check Anchor would auto-generate must be present by hand.
- **Pinocchio:** `no_std`, zero-copy accounts, `unsafe` pointer casts; much faster and far easier to get wrong — scrutinize every `unsafe` and slice bound.

## Account model and the checks that matter

- **Owner check:** `account.owner == program_id`. Without it, an attacker passes an account owned by another program.
- **Signer check:** `account.is_signer`. Skipping it lets anyone act as the authority.
- **Mutability:** `account.is_writable` in native code; Anchor's `mut`.
- **Type/discriminator:** Anchor stores an 8-byte discriminator; a raw `AccountInfo` re-interpreted as the wrong type is account-confusion.
- **Duplicate accounts:** the same mutable account passed twice (as both source and destination) bypasses balance math.
- **`close` / reinit:** Anchor `close = recipient` zeroes lamports and data; failing to close strands an account or allows later reinit that resets authority.

## PDAs, seeds, and CPIs

- **PDA derivation:** `find_program_address(&[seeds], program_id)`; the program signs via `invoke_signed` with the same seeds and bump.
- **Seed collision:** short or ambiguous seeds (no separator) let two logical accounts share a PDA. Prefer fixed prefixes plus unique keys.
- **Bump:** store and reuse the canonical bump; recomputing a different bump finds a different address.
- **Arbitrary CPI:** an unchecked CPI target is an attacker-supplied program — constrain `program.key == expected_program::ID`. See `vulnerabilities/solana-cpi-safety`.
- **`invoke_signed` signer seeds** must match the PDA exactly, or the wrong authority signs.

## Tokens

- **SPL Token:** `token::transfer` via CPI; validate mint, authority, decimals, and the token program id.
- **Token-2022 extensions:** transfer fees, transfer hooks (`on_transfer`), permanent delegate, confidential transfers, non-transferable, interest-bearing. A hook can re-enter; a fee changes the amount received. The two programs are distinct — a hardcoded `spl_token::ID` breaks on a Token-2022 mint.
- **Associated Token Account (ATA):** `associated_token::mint`/`authority` constraints verify the ATA is real.

## Compute budget

- Default 200k CU per instruction, 1.4M per tx; `set_compute_unit_limit`/`set_compute_unit_price`.
- Unbounded iteration over accounts or data is a DoS — the tx hits the CU limit and fails. Bound loops or paginate.
- `msg!` logging costs CU; a debug-heavy path can exceed the budget.

## Toolchain & build

- `cargo build-sbf` (SBF toolchain) produces the deployable program; `anchor build`.
- `solana-test-validator` for a local chain; `anchor test` boots it, deploys, and runs the `test/` clients.
- **LiteSVM:** in-process SVM for fast Rust tests (`LiteSVM::new()`, `set_account`, `add_program`).
- **Trident** and `cargo fuzz` for fuzzing entry points with random account/instruction combinations.

## Where the bugs live

- **Missing signer check** — an authority action without `is_signer`.
- **Account owner/type confusion** — a raw `AccountInfo` cast to a state struct; discriminator not checked.
- **PDA seed collision** — ambiguous seeds.
- **Arbitrary CPI** — unchecked `program_id` in `invoke`.
- **Account closing / reinit** — missing `close`, or a reinit that resets authority.
- **Unchecked arithmetic** — native `+`/`-` wrap in release unless `checked_*`; Anchor `Overflow` only on its checked math.
- **Token-2022 extensions** — hooks, fees, permanent delegate.
- **Duplicate mutable account** — aliasing.
- **Sysvar/clock spoofing** — passing a fake clock account instead of `Clock::get()`.

## Proof standard

A Rust integration test against `solana-test-validator` or LiteSVM that constructs the malicious instruction(s) with attacker-controlled accounts and asserts the unauthorized state change or drained lamports/tokens, printing the account diffs. A bare code-read is a **lead**; the confirmed finding names the exact accounts and the missing check. See `tooling/solana-anchor`.

## Testing

- `anchor test` for the happy path and privilege-escalation cases.
- LiteSVM for unit-level account manipulation with full control of owner/signers/data.
- `trident fuzz` / `cargo fuzz` for account-combination fuzzing.
- Assert on `process_instruction` return codes for the negative cases.

## Fix patterns

`#[account(owner = …, signer, mut, has_one = …)]` on every field; explicit `if account.owner != program_id { return Err(...) }` in native; check `program.key` before every CPI; store the canonical bump; `checked_add`/`checked_sub`; close accounts explicitly; handle both token programs; bound all iteration.
