---
name: move-security-checklist
description: Sui and Aptos Move security checklist — abilities, visibility, shared objects, dynamic fields, capabilities, arithmetic, and upgrade policy
---

# Move Security Checklist (Sui / Aptos)

A checklist for reviewing Sui Move and Aptos Move. Move's type system enforces resource safety, so the bugs are in *authority and visibility*: who can call a function, what an ability lets a caller do to a resource, and what an upgrade can change. Distilled from Trail of Bits' *Not So Smart Contracts (Sui)*, the Move Prover material, and Sui/Aptos audit checklists.

## Abilities

- [ ] **`copy` on a value type** — a capability/fee/asset copyable, defeating scarcity. Prevent: no `copy` where uniqueness matters.
- [ ] **`drop` on an obligation** — a receipt/debt that can be silently discarded. Prevent: remove `drop` from types that must be consumed.
- [ ] **`store` too broadly** — a type that can be stored, wrapped, or transferred by anyone. Prevent: minimize `store`; keep sensitive types non-`store`.
- [ ] **`key` misuse** — adding `key` without the required `id: UID`/`address`. Prevent: verify `id` handling and the `id_leak` rules.

## Visibility and entry

- [ ] **Over-broad `public`** — an internal state-mutating function is `public` (or `public(friend)` widened). Prevent: narrow to `entry`/`public(friend)`/private.
- [ ] **`public(friend)` trust** — a friend module can call a privileged function. Prevent: audit every friend grant.
- [ ] **`entry` without authority check** — a transaction-callable function that trusts its arguments. Prevent: verify the caller/signer and object ownership.
- [ ] **`init` / one-time witness** — a witness that can be forged, or an `init` that leaves a capability unset. Prevent: enforce the OTW pattern and capability creation.

## Capabilities and authority

- [ ] **Capability returned to caller** — `AdminCap`/`TreasuryCap` handed out or `store`-able. Prevent: keep caps private and non-`store`.
- [ ] **Capability type confusion** — a generic cap usable for the wrong object. Prevent: bind caps to a type/ID.
- [ ] **Witness/one-time-witness reuse** — a witness that can be constructed twice. Prevent: OTW with the module-name type and `drop` only.

## Shared objects and object identity (Sui)

- [ ] **Unvalidated shared object identity** — a function accepts any shared object of the correct type without ID validation. Prevent: check `object::id`.
- [ ] **Missing object uniqueness** — no one-per-address constraint allows duplicate singleton objects. Prevent: enforce uniqueness on create.
- [ ] **Mutable reference shadowing** — a destructured `mut` binding silently fails to write through to struct fields. Prevent: write back explicitly and test the mutation.
- [ ] **Type parameter griefing** — a caller substitutes a wrong generic type to destroy state before validation. Prevent: validate types before mutating.
- [ ] **Runtime-limit DoS on shared objects** — hard runtime limits abort, causing permanent denial of service. Prevent: bound per-call work.

## Dynamic fields

- [ ] **Dynamic field key collision** — two logical keys map to the same dynamic field key. Prevent: namespace keys; include the type.
- [ ] **Orphaned dynamic fields** — fields not removed when the parent object is consumed/transferred.
- [ ] **Wrapped object misuse** — a wrapped object's authority recoverable by the wrong caller.

## Arithmetic

- [ ] **Integer overflow / abort** — Move aborts (not wraps) on overflow; an attacker can trigger aborts for DoS. Prevent: checked math and explicit bounds.
- [ ] **Division / rounding** — truncation in share, fee, and reward math. Prevent: multiply before divide; define rounding (`vulnerabilities/precision-rounding`).
- [ ] **u8/u16/u32/u64/u128/u256 casting** — silent narrowing. Prevent: explicit, checked casts.

## Upgrade policy

- [ ] **Upgrade-compatibility** — changing struct layout or function signatures under a compatible policy. Prevent: additive-only changes; review the policy.
- [ ] **Verifier bypass via package upgrade** — adding `key` ability on upgrade bypasses the `id_leak_verifier`. Prevent: re-verify on every upgrade.
- [ ] **Publish/mutable policy** — whether the package can be upgraded at all, and by whom.

## Sources

- Trail of Bits *Not So Smart Contracts (Sui)* — Mutable Reference Shadowing, Unvalidated Shared Object Identity, Verifier Bypass via Package Upgrade, Runtime Limit DoS, Missing Object Uniqueness, Type Parameter Griefing: https://github.com/crytic/building-secure-contracts/tree/master/not-so-smart-contracts/sui
- Move Prover (formal specification and verification): https://github.com/move-language/move/tree/main/language/move-prover
- Companion skills: `vulnerabilities/access-control`, `vulnerabilities/upgradeability-proxy`, `analysis/spec-to-code`.
