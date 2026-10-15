---
name: solana-pda-seeds
description: Solana PDA seed bugs - collisions, missing or unvalidated seeds, non-canonical bump, mutable-input seeds, cross-user PDA takeover, create vs find_program_address
---

# PDA Seed Derivation & Collision (Solana)

Program-Derived Addresses are the identity primitive of Solana programs. A PDA is only as
strong as its seed palette: ambiguous, attacker-chosen, or unvalidated seeds let one user
occupy another user's account or share a single PDA across unrelated roles.

## Where to look

- **`find_program_address` vs `create_program_address`** — `Pubkey::find_program_address(&seeds,
  &program_id)` searches bumps `255..=0` and returns the canonical `(pda, bump)`; it cannot
  fail. `create_program_address` accepts a caller-supplied bump and **can** return an off-curve
  address that is not the canonical PDA. Storing a bump but validating with
  `create_program_address` instead of re-deriving is a bug.
- **Bump not stored / not canonical** — if the bump is recomputed or taken from instruction
  data instead of stored, an attacker supplies a different valid bump (or the runtime
  `find_program_address` result diverges) and derives a *second* PDA for the same seeds.
- **Seed collisions from concatenation** — seeds are hashed without delimiters, so `[b"user",
  b"alice"]` and `[b"userab", b"ice"]`... better example: `[b"pool", mint_a, mint_b]` equals
  `[b"pool", mint_a']` when `mint_a' == mint_a || mint_b` if seeds are joined and re-split.
  Always use fixed-length seeds or a length-prefix/delimiter, and prefer typed seeds
  (`mint.key()`, `user.key()`) over free-form `String`/`Vec<u8>`.
- **Seeds derived from mutable input** — a seed built from an account field the user can change
  (a display name, an index the caller passes, a `nonce` supplied in instruction data) lets the
  attacker choose which PDA they land in, or forces a migration.
- **Cross-user PDA takeover** — a PDA whose seeds omit the owner (e.g. `[b"vault"]` for a
  per-user vault, or `[b"vault", id]` where `id` is caller-chosen) means only one vault exists,
  or user B reaches user A's. Include `authority.key()` / `owner.key()` in the seed set.
- **Unvalidated seeds at use site** — Anchor `#[account(seeds = [...], bump)]` re-derives and
  compares; a raw `AccountInfo` with `create_program_address` recomputed inside the handler is
  only as safe as the seeds supplied there.
- **`seeds::program`** — Anchor lets a PDA be derived under a specified program id; ensure the
  program in the seed matches the intended owner, not an attacker-chosen program.
- **CPI `invoke_signed` seeds** — the signed seeds must equal the PDA's true derivation, or the
  signer privilege is granted to the wrong account (see `vulnerabilities/solana-cpi-safety`).

## Attack plan

1. For each PDA, identify its complete seed set and where the bump is stored.
2. Ask: does any seed come from instruction data or mutable account state? If so, the attacker
   chooses the PDA.
3. Ask: does the seed set include the owning user/authority? If not, two users share one PDA.
4. Check for concatenation ambiguity across all seed sets of the same program.
5. Re-derive the PDA with `find_program_address` and compare to the account supplied.

## Proof

- Unit test the derivation directly:

```rust
let (pda, bump) = Pubkey::find_program_address(&[b"vault", user.key().as_ref()], &crate::ID);
assert_eq!(pda, ctx.accounts.vault.key()); // fails => attacker controls the PDA
```

- Integration: `anchor test` / LiteSVM. Pass an alternative bump or a caller-chosen seed
  component and show the instruction accepts an account it should reject, or show user B's
  instruction operating on user A's PDA. A `solana-program-test` case holding two user keys and
  demonstrating takeover is a complete reachable trace.

## Fix

Use `find_program_address` (Anchor's `seeds`/`bump` constraints do this) and store the returned
bump; validate with re-derivation, never with a caller-supplied bump. Build seeds from
fixed-length typed keys, include the owner/authority, and avoid free-form or mutable inputs.
See `ecosystems/solana`, `tooling/solana-anchor`, `vulnerabilities/solana-cpi-safety`.

## Do not flag

Documents that intentionally use a global singleton PDA (e.g. one program config) — that is the
design; confirm only that the seeds are not attacker-influenced.
