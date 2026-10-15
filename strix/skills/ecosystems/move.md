---
name: move
description: Move ecosystem playbook — Sui and Aptos; object/ability model, visibility, shared objects, dynamic fields, and the Move bug-class map
---

# Move Ecosystem (Sui & Aptos)

Move is resource-oriented: values have **abilities** and cannot be copied or dropped unless declared. Sui adds an **object model** (owned, shared, or immutable objects); Aptos stores resources under `signer` addresses. The type system prevents whole bug classes, so the bugs that remain are about **authority, visibility, and object aliasing**.

## When to use

- Sui Move (`sources/*.move`, `Move.toml`, `sui move`) or Aptos Move (`aptos move`, `Move.toml`).
- Code using `public(friend)`, `entry`, `transfer`, shared objects, dynamic fields, or capability types.
- You need the bug-class map before narrowing to `tooling/move-cli`.

## Sui vs Aptos

- **Sui:** objects carry a `sui::object::UID` and abilities `store, copy, drop, key`. Objects are owned (single owner), **shared** (anyone can use in a tx, ordered by consensus), or immutable. `init` runs once at publish.
- **Aptos:** resources are stored under accounts via `move_to`/`move_from`; a `&signer` is required to store. `public(friend)` grants module-level call access.
- **Abilities:** `copy`, `drop`, `store`, `key`. A struct without `drop` must be consumed; without `copy` it cannot be duplicated. A wrongly assigned ability (a `key` struct that should not be freely transferable) is a real bug.

## Visibility and entry points

- **`public`** — callable by any module.
- **`public(friend)`** — callable only by listed friend modules; read the friend list.
- **`public(package)`** (newer Move) — package-scoped.
- **`entry`** — a Sui tx entry; `public entry` is both. An `entry` function that should be `public(friend)` is an access-control hole.
- **`init`** runs at publish; on Aptos it takes `&signer`, on Sui `&mut TxContext`. Initialization that trusts pre-existing stored data is an upgrade hazard.

## Sui objects, dynamic fields, shared state

- **Shared objects** can be mutated by any tx (subject to consensus ordering); no per-sender assumption holds, and contention is a liveness/DoS surface.
- **Dynamic fields (`dynamic_field`, `dynamic_object_field`):** keys are typed; a key that is not unique per logical entry aliases another.
- **`transfer::transfer` vs `public_transfer` vs `share_object`:** a missing transfer can leave a `key` object owned by the module (stuck or stealable).
- **One-time witness (OTW):** `init` receives a witness type named after the module; a fake OTW (same name, different package) or a leaked witness breaks treasury authorization.
- **Capabilities:** `TreasuryCap`/`AdminCap` possession equals authority; a reachable mint of a capability, or storing it in a shared object, hands authority out.

## Aptos resources

- `move_to(&signer, resource)` stores; `move_from<Resource>(addr)` removes and requires authority.
- `borrow_global`/`borrow_global_mut` abort if the resource is absent — a missing existence check is a DoS.
- Only a `&signer` can store under its address; a function taking `&signer` must confirm it is the intended authority (`signer::address_of`).

## Toolchain & build

- **Sui:** `sui move build`, `sui move test`, `sui client publish`; test attributes `#[test]`, `#[test_only]`, `#[expected_failure]`.
- **Aptos:** `aptos move compile`, `aptos move test`, `aptos move prove`, `aptos move publish`.
- **Move Prover** (`aptos move prove`): specs in `spec` blocks (`aborts_if`, `ensures`, `invariant`). Proves only what the specs say.
- `sui move test --coverage`; the Move CLI/language server via `tooling/move-cli`.

## Where the bugs live

- **Capability / authority misuse** — a `Cap` reachable without its intended check; minting without `TreasuryCap`.
- **Visibility** — an `entry`/`public` function that should be `public(friend)`; over-broad friend lists.
- **Resource & ability misuse** — missing `drop`/`copy`; a `key` struct stored where a plain struct belongs; wrap/unwrap leaving a dangling `UID`.
- **Integer overflow / abort** — Move arithmetic aborts on overflow, but `u64`↔`u128` `as` casts truncate; division by zero aborts.
- **Object & dynamic-field aliasing** — a reused `UID`/key; a silently overwritten dynamic field.
- **Shared-object contention (Sui)** — a hot shared object used as a lock; ordering assumptions across txs.
- **Witness / OTW** — a leaked or duplicated one-time witness; a witness another module can construct.

## Proof standard

A `sui move test` / `aptos move test` that constructs the malicious call sequence (wrong signer, forged witness, aliased object, cross-module call) and asserts the unauthorized effect — mint, transfer of a non-owned object, or state corruption. For Sui ordering, a reproducible bad interleaving. A code-read without a passing test is a **lead**.

## Testing

- Sui: `sui move test`; `test_scenario::begin` simulates multiple senders and txs.
- Aptos: `aptos move test`; `#[test(account = @0x1)]` and `#[expected_failure(abort_code = …)]`.
- Move Prover specs for invariants; property tests via `#[test]` loops.
- Inspect storage/objects before and after the call.

## Fix patterns

Restrict with `public(friend)`/`public(package)` and audit friend lists; gate mint/burn on `TreasuryCap`/`AdminCap` existence and ownership; assign abilities minimally; validate `signer::address_of` against the expected authority; use typed wrappers for unique dynamic-field keys; bound shared-object operations; keep OTW witnesses private and single-use.
