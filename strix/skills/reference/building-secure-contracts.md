---
name: building-secure-contracts
description: Development-guideline checklist distilled from Trail of Bits building-secure-contracts plus the crytic not-so-smart-contracts per-chain pitfall families
---

# Building Secure Contracts

A defensive checklist distilled from Trail of Bits' *Building Secure Contracts* development guidelines and the crytic *Not So Smart Contracts* per-chain pitfall catalog. Use the guidelines to judge whether the code was *designed* to be safe, and the per-chain lists as a final sweep for language-specific footguns. Pair it with `reference/scsvs-checklist` and `reference/smart-contract-vulnerabilities`.

## Development guidelines

### High-level design

- [ ] **Document the threat model and invariants** before coding; keep them current (`reconnaissance/threat-modeling`).
- [ ] **Prefer simplicity and reuse** — fewer lines, battle-tested libraries; complexity hides bugs.
- [ ] **State and test the invariants** the system must always hold (`analysis/invariant-discovery`).
- [ ] **Bound every loop and input** so no caller can force an unbounded operation (DoS / gas).
- [ ] **Decide upgradeability deliberately**; if upgradeable, plan storage layout and initializers up front.

### Access control

- [ ] **Name every privileged action and its role**; enforce with modifiers, not naming convention.
- [ ] **Authorize on authenticated origin** (`msg.sender`), never `tx.origin` or an unchecked sender.
- [ ] **Protect initializers** against front-running; lock them once (`analysis/insecure-defaults`).
- [ ] **Least privilege** — no single EOA controls critical funds; timelock/msig admin actions.

### Arithmetic

- [ ] **Use checked math** or a safe library; audit every `unchecked` block, cast, and division.
- [ ] **Handle rounding deliberately** — round against the user; avoid divide-before-multiply (`vulnerabilities/precision-rounding`).
- [ ] **Watch decimals and scale**; never mix tokens of different precision without normalization.
- [ ] **Beware `type(uint).max` sentinels** and arithmetic that can wrap near limits.

### External calls

- [ ] **Check every return value**; do not ignore low-level call success or failure.
- [ ] **Apply checks-effects-interactions** and reentrancy guards around external calls.
- [ ] **Whitelist/validate every call target**; never `delegatecall` into caller-supplied code.
- [ ] **Assume tokens are hostile** — fee-on-transfer, rebasing, non-standard returns (`reference/weird-erc20`).
- [ ] **Treat oracle output as untrusted** — validate freshness, bounds, and sign (see below).

### Upgradeability

- [ ] **Use a maintained proxy pattern** (transparent / UUPS / beacon) with reviewed code (`vulnerabilities/upgradeability-proxy`).
- [ ] **Preserve storage layout** — append-only; never reorder or remove slots.
- [ ] **Protect the upgrade path** with a timelock/msig and test the upgrade end to end.
- [ ] **Disable initializers on the implementation** and initialize atomically.

## Per-chain pitfalls

Short sweep lists; the ecosystem playbooks (`ecosystems/*`) give depth.

### EVM

- [ ] Reentrancy across callbacks; `tx.origin` auth; `delegatecall` to untrusted; unchecked low-level calls.
- [ ] Integer overflow in `unchecked`/casts; rounding; ERC-20 quirks; ERC-4626 inflation.
- [ ] Oracle/price manipulation and flash-loan amplification; signature replay; proxy storage clashes.

### Solana

- [ ] Missing signer/owner checks; account type confusion; PDA seed collisions.
- [ ] Arbitrary CPI targets; unchecked arithmetic; account closing and reinit; Token-2022 extensions.
- [ ] Duplicate mutable accounts; sysvar/clock spoofing; unvalidated remaining accounts.

### Cosmos

- [ ] Address canonicalization (bech32 vs `Addr` vs string); unchecked `info.funds`.
- [ ] `Reply`/submessage and `sudo` handling; migration/admin abuse; unbounded iteration.
- [ ] Decimal/`Uint128` rounding; store key collisions; module/keeper authority.

### Cairo

- [ ] `felt252` overflow and division; `u256`/`i128` conversions; array bounds.
- [ ] Storage address collisions and legacy maps; L1↔L2 message trust.
- [ ] Upgrade/`class_hash` control; hints/oracles as trust holes; access control on `ContractAddress`.

### Substrate / ink!

- [ ] `ensure_signed`/origin misuse; unguarded dispatchables; `#[payable]` on value paths.
- [ ] Storage layout/packing changes; unbounded iteration; `Weight` accounting errors.
- [ ] Contract→contract call reentrancy; trait/ABI mismatch; unchecked `Result`.

### Algorand

- [ ] Missing `Txn.sender`/group checks; inner-transaction rekey, close, and asset-transfer.
- [ ] Unchecked `Txn` fields (fee, rekey-to, close-to); group transaction ordering assumptions.
- [ ] `uint64` overflow; `global`/`local` state and box-storage assumptions.

### TON

- [ ] Sender spoofing (internal vs external, `sender_address`); bounce handling.
- [ ] Cell depth/gas bombs; get-method assumptions; jetton `transfer_notification` trust.
- [ ] Message-mode flags; uninitialized-state reuse; storage-fee/gas draining.

### Cardano (eUTxO)

- [ ] Double satisfaction — one output satisfies several validators; always validate the continuing output.
- [ ] Untrusted datum/redeemer/`ScriptContext`; purpose confusion; `tx.info.signatories` vs owner checks (`vulnerabilities/cardano-datum-redeemer-context`).
- [ ] Native-token forgery and non-one-shot minting; `Value` normalization; lovelace minimums (`vulnerabilities/cardano-value-and-minting`).

## Sources

- Trail of Bits Building Secure Contracts: https://github.com/crytic/building-secure-contracts
- crytic Not So Smart Contracts: https://github.com/crytic/not-so-smart-contracts
