---
name: solana-signer-authorization
description: Solana signer and authorization bugs - missing is_signer checks, unvalidated authority accounts, Signer type bypass, CPI signer-seed misuse
---

# Missing Signer & Authorization Checks (Solana)

On Solana an action is authorized by *which accounts signed*, not by a caller identity. If a
privileged instruction consumes an authority account without proving `is_signer`, anyone can
act as that authority by naming the victim's pubkey in the account list.

## Where to look

- **`AccountInfo` / `UncheckedAccount` authority fields** — Anchor's `Signer<'info>` enforces
  `is_signer`; a raw `AccountInfo` enforces nothing. Grep every handler that takes an authority
  as `AccountInfo` or `UncheckedAccount`.
- **`#[derive(Accounts)]` gaps** — `#[account(signer)]` or `Signer<'info>` must sit on the
  *authority*, not a look-alike. The generated `try_accounts` only validates declared
  constraints; anything undeclared is free.
- **`has_one` / `constraint`** — `#[account(has_one = authority)]` ties an owned data account to
  the pubkey stored inside it. Without it an attacker passes their own data account whose
  `authority` field is their own key, and the victim's real account is never touched.
- **Authority stored but never compared** — instruction takes `authority: Signer<'info>` and
  `vault: Account<'info, Vault>`; if the body never asserts `vault.authority == authority.key()`,
  the signer is decorative and any signer passes.
- **`Signer` type bypass** — `Signer::try_from(&account_info)?` correctly rejects non-signers,
  but re-wrapping a previously stored `AccountInfo` later, or caching `account_info.is_signer`
  into a bool and trusting the bool after a CPI, defeats it.
- **CPI signer seeds** — `invoke_signed(ix, accounts, &[&[seed, &[bump]]])` makes the program
  sign as any PDA it owns. Attacker-influenced or unvalidated seeds let a CPI impersonate an
  arbitrary PDA authority; verify `find_program_address(seeds, program_id) == pda.key()`.
- **Rent/fee-payer confusion** — the account declared `payer` is not automatically the
  authority; confirm which key is actually checked.
- **Program-owned `system_program::transfer`** — a PDA moving lamports needs `invoke_signed`;
  a plain `invoke` that "signs" via a user signer silently transfers the wrong account's funds.

## Attack plan

1. List every state-changing instruction and its authority/owner account.
2. Classify enforcement: by type (`Signer`), by constraint (`signer`, `has_one`), or by an
   inline `require!(account.is_signer, E)` / `if !account.is_signer { return Err(..) }`.
3. For each stored-authority design, check the stored pubkey is compared to the signer's
   `key()`.
4. Trace each `invoke_signed`: can `seeds`/`program_id` be influenced, and is the signed PDA
   then used as an authority in the child instruction?
5. Submit the zero-signature path — only the fee payer signs.

## Proof

- Anchor: `anchor build && anchor test` with a test that marks the authority account
  non-signer and asserts the instruction errors, plus a patched copy that succeeds.
- Native: a `solana-program-test` or LiteSVM test proves the missing check directly:

```rust
let mut svm = LiteSVM::new();
svm.add_program_from_file(program_id, "target/deploy/prog.so")?;
let payer = Keypair::new();
svm.airdrop(&payer.pubkey(), 1_000_000_000)?;
// attacker is the fee payer only; expected authority is NOT in the signer list
let tx = Transaction::new_signed_with_payer(
    &[ix], Some(&payer.pubkey()), &[&payer], svm.latest_blockhash());
let res = svm.send_transaction(tx); // must be Err on a correct program
```

Show the failing (correct) case and the succeeding (patched) case. A raw instruction log with
`solana logs --verbose` naming signer privileges is acceptable trace evidence at lower severity.

## Fix

Use `Signer<'info>` for every authority; add `#[account(has_one = authority)]` on owned data
accounts; assert `signer.key() == stored_authority` explicitly. Validate CPI seeds with
`find_program_address` before `invoke_signed`. See `tooling/solana-anchor`, `ecosystems/solana`.

## Do not flag

Fee-payer or rent-payer accounts that legitimately need no authority, and instructions designed
to be permissionless (a crank, an oracle push) — confirm the emitted effect is genuinely public.
