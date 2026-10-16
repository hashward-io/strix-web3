---
name: sway-security-checklist
description: Sway/Fuel security checklist — predicates and their data, storage and configurables, asset and msg_sender handling, cross-contract reentrancy
---

# Sway / Fuel Security Checklist

A checklist for reviewing Sway contracts, predicates, and scripts on Fuel. Fuel separates **predicates** (stateless spend conditions), **scripts** (stateless one-shots), and **contracts** (stateful). The distinctive bugs are **predicate assumptions**, **`msg_sender`/asset confusion**, and **configurable constants**.

## Predicates & scripts

- [ ] **Predicate reads state it does not own** — a predicate assumes mutable state or an external contract call; predicates are stateless and evaluated against the transaction only (`vulnerabilities/sway-storage-and-predicates`).
- [ ] **Unvalidated predicate data** — `predicate_data` accepted without checking it encodes the intended condition.
- [ ] **Configurable set incorrectly** — a `configurable` admin/owner/slot is not committed to at deploy time, or a predicate depends on a configurable that a spender can set.
- [ ] **Anyone-can-spend branch** — a predicate/script that returns `true` on a path reachable by an attacker.

## Storage & configurables

- [ ] **Storage-key collision** — `StorageMap` readers/writers keyed so two logical maps overlap (`vulnerabilities/sway-storage-and-predicates`).
- [ ] **Missing `#[storage(...)]` attributes** — a read/write method not annotated, or an overflow in a storage key.
- [ ] **Unstructured storage in `#[namespace]`** — assumptions about slot layout across a proxy upgrade.

## Assets & sender

- [ ] **`msg_sender` confusion** — `msg_sender().unwrap()` is the *immediate* caller (a contract on a cross-contract call), not the end user; also `None` in a script (`vulnerabilities/sway-arithmetic-and-reentrancy`).
- [ ] **Forwarded asset not validated** — `msg_amount()` / `this_balance(asset_id)` trusted without checking the `AssetId`.
- [ ] **Unchecked mint/burn** — an asset operation without an owner/role check.

## Arithmetic & reentrancy

- [ ] **Unchecked math** — Fuel's `u64` (and `u256`) arithmetic wrapping; missing `overflow`/`saturating` handling.
- [ ] **Reentrancy across contracts** — state read/written after a `call`, without following checks-effects-interactions.

## Validation

- [ ] Reproduce with `forc test` / `fuel-core` in a local node: craft a malicious transaction, spoof a cross-contract caller, or exercise the predicate data, asserting the unauthorized state change.
- [ ] `forc build` and compare the deployed predicate/contract bytecode and configurables against source.
