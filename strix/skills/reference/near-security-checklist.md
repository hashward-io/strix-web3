---
name: near-security-checklist
description: NEAR security checklist — predecessor vs signer, promises and callbacks, storage staking, attached deposit, access keys and gas
---

# NEAR Security Checklist

A checklist for reviewing NEAR contracts (`near-sdk` in Rust, `near-sdk-as` in AssemblyScript). NEAR is **sharded and asynchronous**: cross-contract calls are promises resolved in a later block, and the runtime charges **storage staking** (locked NEAR per byte). The distinctive bugs are **`predecessor_account_id` vs `signer_account_id`**, **promise trust**, and **attached deposit**.

## Identity & authorization

- [ ] **`predecessor` vs `signer` confusion** — authorizing on `env::predecessor_account_id()` when the caller is a relayer, or on `signer` when the direct caller matters (`vulnerabilities/near-access-and-math`).
- [ ] **Missing `#[payable]` check** — a method that must be paid is callable with zero attached deposit, or vice versa.
- [ ] **Re-initialization** — a plain public method that writes initial state after `#[init]`, letting anyone re-init.
- [ ] **Unchecked access-key class** — assuming a function-call access key cannot do damage when the method is unauthenticated.

## Promises & callbacks

- [ ] **Trusting a callback's predecessor** — a `.then` callback authorizes on `predecessor_account_id`, which is the *contract that sent the promise*, not the original caller (`vulnerabilities/near-promise-and-storage`).
- [ ] **State finalized before the callback** — crediting a deposit/withdrawal in the first call when the promise may fail or resolve later.
- [ ] **Unhandled promise failure** — a failed cross-contract call leaves state inconsistent.
- [ ] **`promise_result` not matched to the right promise** — reading the wrong result index in a chained callback.

## Storage & funds

- [ ] **Storage-staking griefing** — a method that writes unbounded data to a non-payer's account, or a refund that is not stored (`vulnerabilities/near-promise-and-storage`).
- [ ] **Attached-deposit accounting** — `env::attached_deposit()` credited without checking the account can cover storage.
- [ ] **Unbounded iteration** — a `Vector`/`UnorderedMap` loop that exceeds gas.

## Arithmetic

- [ ] **Overflow / truncation** — yoctoNEAR math, `u128`/`u64` casts, and rounding on shares (see `vulnerabilities/precision-rounding`).

## Validation

- [ ] Reproduce with `near-workspaces` (sandbox): impersonate a predecessor, call an unpaid method, trigger a failing promise, or write unbounded state, asserting the unauthorized state change.
- [ ] Confirm the `#[init]`/re-init guard and every `predecessor`/`signer` decision against the actual runtime semantics.
