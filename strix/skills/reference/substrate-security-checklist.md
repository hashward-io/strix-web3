---
name: substrate-security-checklist
description: Substrate/ink! security checklist — dispatch origin, storage layout and packing, weights and fees, cross-contract calls, ABI
---

# Substrate / ink! Security Checklist

A checklist for reviewing ink! contracts and Substrate runtime pallets. The trust boundaries are **dispatch origin**, **storage layout**, and **weights** (the runtime pays for compute by weight, not gas). The distinctive bugs are **origin confusion**, **storage packing/layout errors**, and **unaccounted weight**.

## Dispatch & origin

- [ ] **Origin not checked** — a dispatchable (`#[ink(message)]` / pallet `call`) that mutates privileged state without checking `ensure_signed`/`ensure_root` or the caller (`vulnerabilities/substrate-dispatch-origin`).
- [ ] **`Origin::Signed` vs `Root`** — a privileged action reachable by any signed account.
- [ ] **Caller identity via `self.env().caller()`** — trusted through a cross-contract call (the caller is the calling contract, not the end user).

## Storage & layout

- [ ] **Storage packing** — `#[ink(storage)]` field ordering that causes unintended packing/unpacking, or a `Mapping` key collision (`vulnerabilities/substrate-storage-and-weight`).
- [ ] **Storage migration** — a runtime upgrade / contract upgrade that changes the layout without a migration, or an unauthenticated `set_code` (`vulnerabilities/ink-storage-and-abi`).
- [ ] **Lazy vs eager** — an operation assumed atomic that is actually spread across blocks.

## Weight, fees & DoS

- [ ] **Unaccounted weight** — an unbounded loop or storage iteration in a dispatchable, exceeding the block weight or letting an attacker exhaust it (`vulnerabilities/substrate-storage-and-weight`).
- [ ] **Fee/weight refund** — a path that lets a caller do unbounded work for a fixed fee.
- [ ] **Panic instead of revert** — a trap in a path that should return a `DispatchError`, bricking state.

## Cross-contract calls & ABI

- [ ] **Untrusted callee** — calling a contract/trait whose address/`code_hash` is attacker-controlled.
- [ ] **Reentrancy across contracts** — state read after a cross-contract call.
- [ ] **Selector / ABI mismatch** — a trait implementation whose selectors or argument encoding differ from what the caller assumes.

## Validation

- [ ] Reproduce with `ink_e2e`/`ink` unit tests or a Substrate test runtime: call an unguarded dispatchable, exercise the storage boundary, or exhaust weight, asserting the unauthorized state change.
- [ ] `cargo contract build` and confirm the metadata/ABI and storage layout match the deployed contract.
