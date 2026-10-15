---
name: solana-security-checklist
description: Solana program security checklist — signer, owner, PDA, CPI, account close/reinit, arithmetic, Token-2022, and fuzzing
---

# Solana Security Checklist

A checklist for reviewing Solana programs (Anchor, native, Pinocchio; Token and Token-2022). Distilled from Trail of Bits' *Not So Smart Contracts (Solana)* and Solana audit checklists. Every instruction deserializes caller-supplied accounts, so most bugs are missing validations on those accounts, not exotic cryptography.

## Account validation

- [ ] **Missing signer check** — `is_signer` not enforced on an authority. Prevent: use the `Signer<'info>` type or `require!(authority.is_signer)` (`vulnerabilities/access-control`).
- [ ] **Missing ownership check** — an account is read or written without `account.owner == program_id`. Prevent: `Account<'info, T>` (Anchor) or an explicit owner check.
- [ ] **Account type confusion** — two account types share a size, or a `Vec<AccountInfo>` is not type-checked. Prevent: typed accounts and discriminators.
- [ ] **Duplicate mutable accounts** — the same account passed twice in a mutating instruction. Prevent: `require!(a.key() != b.key())`.
- [ ] **Unvalidated account data** — trusting `data` without deserialization/version checks.
- [ ] **Sysvar account check** — a caller-supplied account used as `Clock`/`Rent`/`Instructions`. Prevent: load sysvars by address.
- [ ] **Missing rent-exemption check** on created accounts.

## PDA and seeds

- [ ] **Improper PDA validation** — a PDA derived with a non-canonical bump can be spoofed. Prevent: `find_program_address`, store the canonical bump, and verify it (Anchor `seeds`+`bump`).
- [ ] **PDA seed collision** — variable-length seeds concatenated without a separator collide. Prevent: length-prefix or delimit seeds.
- [ ] **PDA not bound to authority** — a program-owned global account not tied to the caller. Prevent: include the authority in the seeds and check `has_one`/`constraint`.
- [ ] **Missing `init` guard** — an account that should be created once is re-initializable. Prevent: `init` / `init_if_needed` with a discriminator.

## CPI

- [ ] **Arbitrary CPI** — the callee program account is caller-supplied. Prevent: hardcode/allowlist the program ID before `invoke`.
- [ ] **Unchecked CPI return data** — reusing data from an untrusted callee. Prevent: validate the program ID and parse defensively.
- [ ] **Privilege escalation via CPI** — forwarding signer privileges to an untrusted program.
- [ ] **Arbitrary CPI reentrancy** — a callee that calls back into the program mid-update.

## Instruction introspection

- [ ] **Improper instruction introspection** — matching instructions by absolute index breaks when instructions are prepended. Prevent: match relative to the end or validate the full set.

## Account lifecycle

- [ ] **Reinit after close** — a closed account reused for a different purpose. Prevent: discriminator/close flag; zero data and close in the right order.
- [ ] **Unchecked `close` destination** — closing to a caller-supplied account. Prevent: close to the owner/authority.
- [ ] **Anchor `close` on the wrong account** — closing an account still referenced.

## Arithmetic

- [ ] **Unchecked arithmetic** — `+`/`-`/`*` panic or wrap in release. Prevent: `checked_add`/`checked_mul`/`checked_sub`, or `overflow-checks = true`.
- [ ] **Division and rounding** — integer truncation in share/interest math. Prevent: multiply before divide; define rounding (`vulnerabilities/precision-rounding`).
- [ ] **Unit confusion** — lamports vs token base units vs UI amounts, yocto-style scaling. Prevent: normalize units explicitly.

## Token and Token-2022

- [ ] **Mint/authority not checked** — accepting an arbitrary mint or mint authority. Prevent: validate mint and authority.
- [ ] **Token-2022 extensions** — transfer fee, interest-bearing, permanent delegate, transfer hook, non-transferable, confidential transfer. Prevent: account for fee/rebasing and hook reentrancy.
- [ ] **Associated Token Account** — trusting a caller-supplied ATA. Prevent: derive and check the ATA.
- [ ] **Token program confusion** — passing the wrong token program (legacy vs Token-2022). Prevent: pin the expected program.

## Testing and fuzzing

- [ ] Run **Trident** or **cargo-fuzz** / Honggfuzz over instruction sequences.
- [ ] Write conservation and authority invariants; fuzz state transitions (`custom/fizz-invariants`).
- [ ] Add unit tests for every "missing check" above against a malicious account set.

## Sources

- Trail of Bits *Not So Smart Contracts (Solana)* — Arbitrary CPI, Improper PDA Validation, Ownership Check, Signer Check, Sysvar Account Check, Improper Instruction Introspection: https://github.com/crytic/building-secure-contracts/tree/master/not-so-smart-contracts/solana
- Token integration checklist: https://github.com/crytic/building-secure-contracts/blob/master/development-guidelines/token_integration.md
- Companion skills: `vulnerabilities/access-control`, `vulnerabilities/token-integration`, `vulnerabilities/reentrancy`.
