---
name: solana-account-validation
description: Solana account validation - owner and discriminator checks, type cosplay, PDA vs data mixups, duplicate mutable accounts, unchecked deserialization, sysvar spoofing
---

# Account Validation & Type Confusion (Solana)

Every `AccountInfo` is attacker-supplied bytes until proven otherwise. The runtime checks only
that lamports moved; it does **not** verify owner, type, or uniqueness. Missing owner/type/
discriminator/duplication checks turn one instruction into a confused-deputy over every account
the caller can name.

## Where to look

- **`AccountInfo` without an `owner` check** — `account.owner` is not compared to
  `crate::ID`. A caller can hand you *any* account of the right size. In Anchor, `Account<'info, T>`
  performs this check; `AccountInfo`/`UncheckedAccount` do not.
- **Type cosplay / missing discriminator** — Anchor's 8-byte discriminator is
  `sha256("account:<StructName>")[..8]`. Native code that does `Account::try_from` /
  `AccountDeserialize::try_deserialize` gets it, but `try_from_unchecked`, manual
  `borsh::from_slice`, or a zero-copy cast does not. Passing account A where account B is
  expected succeeds if the byte layouts overlap.
- **`#[account(constraint = ...)]` gaps** — no `owner = ...`, no
  `#[account(owner = my_program::ID)]`, no `address = ...`. For external programs assert the
  program id too, e.g. `#[account(address = anchor_spl::token::ID)]`.
- **PDA vs data-account mixup** — an instruction that treats an arbitrary data account as a
  PDA (or vice versa). `Address<'info>` / `Account<'info, T>` with `seeds` proves derivation;
  a bare `AccountInfo` assumed to be "the vault" does not.
- **Duplicate mutable accounts** — the same account passed twice in two `#[account(mut)]`
  positions. Anchor emits `ConstraintDuplicateMutableAccount` for `Account<'info, T>` mutable
  pairs in recent versions, but `UncheckedAccount`/`AccountInfo` bypass it. Classic case: the
  same token account used as both source and destination to self-inflate a balance.
- **Unchecked deserialization** — `Account::try_from_unchecked`, `try_borrow_data()` then a raw
  pointer cast, `zero_copy` structs without a discriminator, or trusting `Pubkey` fields read
  from account data without comparing them to the instruction's accounts.
- **Sysvar spoofing** — the runtime only special-cases a sysvar account when it is the *actual*
  sysvar id. Native code that deserializes a `Clock`/`Rent` from any account can be fed a fake
  `Clock` (attacker-controlled `unix_timestamp`, `slot`, `epoch`) or `Rent`. Anchor's
  `Sysvar<'info, Clock>` and `Clock::get()` (the syscall) are safe; a manual
  `Clock::from_account_info(&ctx.accounts.clock)` is not unless the id is checked.
- **Missing `executable` / signer sanity** — a program account assumed to be a program but not
  checked for `executable`, or an authority assumed to be a data account but actually a program.

## Attack plan

1. For each account, ask: what proves its `owner`, its type, its address/derivation, and its
   uniqueness relative to the others?
2. Swap in a same-size account owned by a different program; swap in account B for expected A
   (type cosplay); pass the same account twice.
3. Feed a fake sysvar account where a `Clock`/`Rent`/`EpochSchedule` is expected.
4. If a field read from account data drives authority or math, check it is itself validated.

## Proof

- Anchor: `anchor test`. Write a test that passes a forged account (your own program's account
  of the same size, or an account with a wrong owner) and show the instruction succeeds where it
  should error.
- Native: LiteSVM / `solana-program-test` lets you craft the exact `AccountMeta` list:

```rust
let mut svm = LiteSVM::new();
svm.add_program_from_file(program_id, "target/deploy/prog.so")?;
svm.set_account(fake_vault, Account { owner: attacker_program, data, ..Default::default() })?;
let res = svm.send_transaction(tx); // succeeds despite wrong owner => finding
```

For sysvar spoofing, pass a normal account at the slot where the program expects `Clock` and
observe it deserializes. A complete reachable trace in the account list is the minimum bar; a
working PoC upgrades a lead to a finding.

## Fix

Prefer `Account<'info, T>` (owner + discriminator enforced) and `Sysvar<'info, T>`; add
`owner = ...`/`address = ...` constraints; use `Signer`/`Address`/`SystemAccount` deliberately.
Reject duplicate keys (`#[account(constraint = a.key() != b.key())]`) or use
`AccountLoader`/`InterfaceAccount` for type safety. See `ecosystems/solana`, `tooling/solana-anchor`.
