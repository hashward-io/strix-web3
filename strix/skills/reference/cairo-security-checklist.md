---
name: cairo-security-checklist
description: Cairo and Starknet security checklist — felt252 math, storage, L1↔L2 messaging, access control, upgradeability, and hints/oracles
---

# Cairo / Starknet Security Checklist

A checklist for reviewing Cairo contracts on Starknet (and Cairo 1 / Sierra). Cairo's `felt252` field arithmetic and the L1↔L2 message boundary are the two richest sources of bugs. Distilled from Trail of Bits' *Not So Smart Contracts (Cairo)* and Starknet audit checklists.

## felt252 and integer math

- [ ] **`felt252` overflow** — `felt252` arithmetic is modulo the prime; values can wrap without a built-in check. Prevent: use `u256`/`i128` for value math; bound every felt (`vulnerabilities/precision-rounding`).
- [ ] **`felt252` as an integer** — treating a felt as a bounded integer when it can exceed `2^251`. Prevent: range-check before interpretation.
- [ ] **Division / inverse** — `felt252` division does not revert on zero in all cases; misleading truncation. Prevent: use integer types and check the divisor.
- [ ] **Casting `u256` ↔ `i128` ↔ felt** — silent truncation on narrowing. Prevent: explicit checked conversions.
- [ ] **`u256` arithmetic costs and bounds** — overflowing/underflowing limbs. Prevent: use the provided `u256` ops and test boundaries.
- [ ] **Non-normalized boolean felt** — a nonzero `felt252` treated as `true` without normalization to `0`/`1`. Prevent: normalize before branching.

## Storage

- [ ] **Storage address collisions** — manual `storage_base`/`storage_addr` computations that collide between variables or maps. Prevent: use the compiler's storage layout, not hand-rolled addresses.
- [ ] **Legacy maps / `LegacyMap`** — hash collisions between different maps. Prevent: namespace keys; include a domain separator.
- [ ] **Storage packing** — values packed into one felt exceeding the field. Prevent: verify packed widths.
- [ ] **Uninitialized storage** — a default read assumed to be a real value (see `analysis/insecure-defaults`).

## L1 ↔ L2 messaging

- [ ] **L1 to L2 address conversion** — an L1 address not properly converted/validated to a Starknet `ContractAddress`. Prevent: enforce the L2 address check (the `is_valid_l1_to_l2` pattern).
- [ ] **Unchecked `from_address` in an L1 handler** — `#[l1_handler]` trusting the sender. Prevent: validate `from_address` against the expected L1 contract (`vulnerabilities/access-control`).
- [ ] **L1 to L2 message failure** — a message that the sequencer never processes. Prevent: handle delivery failure and refunds.
- [ ] **Overconstrained L1↔L2 interaction** — asymmetric checks on the two sides cause a DoS. Prevent: keep the checks symmetric.
- [ ] **Message replay** — a consumable message processed twice. Prevent: nullifiers/consumed-message tracking.

## Access control and account abstraction

- [ ] **Missing `starknet::ContractAddress` check** — caller/owner not validated. Prevent: compare against stored `ContractAddress`.
- [ ] **`__validate__` / `__execute__` trust** — a custom account that validates less than it should. Prevent: enforce signature and nonce checks.
- [ ] **Owner/role default** — owner storage defaults to `0`; a zero-address `ContractAddress` may pass. Prevent: reject the zero address.
- [ ] **Caller spoofing assumptions** — trusting `get_caller_address` for L2-only callers when an L1 handler can also reach the code. Prevent: validate per entry point.
- [ ] **Signature replay** — account abstraction makes replay protection essential. Prevent: nonce + chain id + contract address in the signed message.

## Upgradeability

- [ ] **`replace_class` / `class_hash` authorization** — upgrade callable by the wrong actor. Prevent: guard the upgrade with the owner/admin.
- [ ] **Upgrade to an arbitrary class** — no validation of the new implementation. Prevent: allowlist or timelock.
- [ ] **Storage layout across upgrades** — inserting/reordering storage under an upgradeable class. Prevent: append-only layout.
- [ ] **Unprotected or instant upgrade** — no owner guard or delay on `replace_class`. Prevent: owner guard plus a timelock.
- [ ] **Migration not run** — an upgrade that changes semantics without a migration entry point to fix stored state.

## Hints, oracles, and randomness

- [ ] **Hints as trusted input** — a `%{ ... %}` hint assumed correct; hints are not part of the proof for on-chain Cairo but can leak or mislead. Prevent: don't trust hints for value.
- [ ] **Price oracle** — spot vs TWAP, stale data, decimals. Prevent: use a validated oracle (`vulnerabilities/oracle-manipulation`).
- [ ] **Nondeterministic values** — a value derived from a hint used in authorization/math.
- [ ] **`block_timestamp` / `block_number`** — used as entropy or an exact clock. Prevent: tolerate drift; never use as randomness.

## Sources

- Trail of Bits *Not So Smart Contracts (Cairo)* — Arithmetic overflow (felt252), L1 to L2 Address Conversion, L1 to L2 message failure, Overconstrained L1↔L2 interaction, Signature replays, Unchecked `from_address` in L1 Handler: https://github.com/crytic/building-secure-contracts/tree/master/not-so-smart-contracts/cairo
- Companion skills: `vulnerabilities/access-control`, `vulnerabilities/precision-rounding`, `analysis/insecure-defaults`.
