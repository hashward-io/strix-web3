---
name: sway-storage-and-predicates
description: Sway storage and predicates — stateless-predicate violations, storage read/write in predicates, StorageMap key confusion, slot collisions, and configurable-constant trust
---

# Sway Storage and Predicates

Sway has three execution contexts: scripts, predicates, and contracts. Predicates are pure boolean gates that are *not* allowed to touch storage; contracts annotate every function with the storage access it performs. Violating either rule, or confusing a `StorageMap` key, is a common and high-impact bug.

## Where to look

- Predicate definitions: `predicate { ... }` and any use of `storage.*` inside them. A predicate that reads storage is invalid (compile error in current Sway) or, historically, a soundness hole — the predicate's truth does not depend on state and can be replayed.
- Storage declarations: `#[storage(read)]`, `#[storage(write)]`, `#[storage(read, write)]` on `abi` and `impl` functions. A function that writes storage but is declared `#[storage(read)]` should not compile — check the annotations match the body.
- `StorageMap`: `storage.map.get(key)`, `.insert(key, val)`, `.try_get`, and the key type. Key confusion = reading under key A and writing under key B (wrong argument, wrong tuple order, string-vs-bytes mismatch).
- Slot layout: `#[storage]` struct field order, `#[namespace(...)]`, and nested/nested-map layout. Manual slot offsets or `__slot` collisions let two logical fields alias one slot.
- Configurables: `configurable { X: u64 = <default> }` — set at deploy time, then trusted forever by the code.

## Attack plan

1. For every predicate, ask: does its validity depend on anything mutable? If the predicate can only read immediate script/message data, fine. If it relies on a constant that governance can change, or on storage it cannot read, the guarantee is weaker than assumed.
2. Predicate replay / soundness: a predicate that is satisfiable once is satisfiable every time its inputs recur. If a contract treats "predicate satisfied" as "one-time authorization", an attacker replays the same valid predicate.
3. StorageMap key confusion: locate every `.get(k)`/`.insert(k, v)` pair for the same logical entry. A mismatch (e.g. `get(user)` vs `insert(asset, user)`) reads a default and writes elsewhere, enabling balance forgery or locking.
4. Key type confusion: hashing a `b256` vs `Address` vs a packed tuple can collide across types if the code unifies them (`asm` hashing, manual key construction). Two different logical keys mapping to one slot.
5. Slot collision: with `#[namespace]` removed or field order changed, two maps can share a slot start. Write through one, read garbage through the other.
6. Configurable trust: a `configurable` used as an authorization value (an admin address, a fee) but initialized by the deployer without a guard — the deployer can set it to themselves. Ask who can influence the config and whether that role is trusted.
7. `#[storage(read)]` on a function that *should* write but does not (or vice versa after a refactor) — the mismatch signals a subtle correctness bug even if it compiles.

## Proof

- `forc test` with `#[test]` functions, using `Test`/`Contract` helpers and `abi(...)` calls; assert the key-confusion or slot-collision outcome.
- `forc build` to confirm storage annotations and to see whether a predicate touching storage is rejected.
- For configurable trust, deploy with an attacker-set configurable and show the privileged path opens.
- For predicate replay, submit the same valid predicate transaction twice.

## Fix

- Keep predicates pure and stateless; never encode mutable protocol state in a predicate. If a one-time check is needed, do it in the contract with storage.
- Make `#[storage(read)]` / `#[storage(write)]` / `#[storage(read, write)]` exactly match the body; rely on the compiler to enforce it and fix the body when it rejects.
- Derive every `StorageMap` key from a single shared helper; use `insert`/`get` with the same key expression and same type.
- Use `#[namespace]` on large storage structs and avoid manual slot offsets; test read/write round-trips after any layout change.
- Treat configurables as trusted input only if the deployer is trusted; validate or immutably fix security-relevant values.

## Context quick reference

- A `predicate` returns `bool` and must depend only on its inputs; it cannot read `storage`.
- Scripts run once and hold no state; contracts own `#[storage]`.
- `#[storage(read)]`, `#[storage(write)]`, `#[storage(read, write)]` are checked by the compiler against the body.
- `StorageMap` keys are hashed; the map has no iteration without an auxiliary index (`StorageVec` of keys).
- `configurable { ... }` values are fixed at deploy and are not upgradeable without redeploy.

## Severity and finding bar

- Storage key confusion that forges or locks balances is **Critical**.
- A storage-touching predicate is **High** (soundness) if it compiles at all.
- A slot collision is **High** when it corrupts value-bearing state.
- An untrusted configurable is **Medium** unless it is an authority value, then **High**.

## See also

- `ecosystems/sway` — the ecosystem playbook.
- `vulnerabilities/access-control`, `vulnerabilities/accounting-conservation` — the general classes.
- `sway-arithmetic-and-reentrancy` — the sibling Sway surface.
