---
name: substrate-storage-and-weight
description: Substrate and ink! storage — packing, lazy Mapping vs eager Vec/StorageVec, iteration DoS, Weight under-estimation, storage migration, set_code_hash upgrade authorization
---

# Substrate and ink! Storage and Weight

Storage is the expensive, persistent, attacker-writable part of a Substrate/ink! contract. How fields are packed, whether collections are lazy, how iteration is bounded, and how upgrades rewrite layout are all correctness-critical.

## Where to look

- Layout: `#[ink(storage)]` struct field order and packing (fields are packed into per-field slots; reordering changes slots).
- Collections: `ink::storage::Mapping<K, V>` is lazy (reads/writes a single entry); `Vec<T>` and `StorageVec<T>` are loaded/iterated element by element. Nested `Mapping` keys and `Mapping<_, Mapping<_, _>>`.
- Iteration: any `for x in self.items.iter()` or `self.storage_vec.iter()` inside a dispatchable — unbounded work.
- Weight / deposit: `#[ink(message)]` without a `Weight` reflection, `ink::env::weight`? Storage deposit APIs, `StorageDeposit` limits, `env().minimum_balance()`.
- Upgrades: `set_code_hash(&code_hash)`, the `ink::env::set_code_hash` path, and the `upgradeable` feature flag.
- Migrations: `#[ink(storage)]` changes across a `set_code_hash` upgrade; the `Migrate` / `on_runtime_upgrade` idiom in FRAME.

## Attack plan

1. Map every storage item and its cardinality. A `Vec<T>` that grows with user input is a bomb: once large enough, *reading* it costs more weight than a block allows, bricking every function that touches it.
2. Iteration DoS: find a loop over a `Vec`/`StorageVec`/`Mapping`-derived key set in a message reachable by anyone. Grow the collection, then call a function that iterates it and show it exhausts the weight limit.
3. Packing bugs: a field written into the wrong slot after a layout change, or two logical values packed into one slot where a write clobbers the neighbour. Compare before/after storage dumps.
4. Lazy vs eager: code that treats a `Mapping` like an in-memory map (expecting `len()` cheaply or order) behaves differently than assumed, or a `StorageVec` that should be a `Mapping` forces O(n) work on a hot path.
5. Weight under-estimation: a dispatchable whose declared weight is below worst-case work can be called repeatedly to fill a block, starving other transactions. Show the actual vs declared weight.
6. Upgrade authorization: `set_code_hash` with no owner check lets anyone replace the contract logic — full takeover. Even when guarded, an unguarded `set_code_hash` reachable through a proxy/multisig is a High.
7. Migration correctness: after `set_code_hash`, old storage is reinterpreted with the new layout. A changed struct without a migration maps old slots to wrong fields (e.g. an `owner` field reading a balance slot).

## Proof

- `cargo contract test` with `ink::env::test` (set `set_value_transferred`, `set_account_balance`, insert storage) to grow a collection and assert the iterating message reverts on weight.
- `cargo contract build` + `cargo contract` metadata to inspect selectors and storage layout; diff layouts across versions.
- For upgrades, deploy v1, `set_code_hash` to v2, and read storage through v2 to show field reinterpretation.
- For weight, use the node's `#[pallet::weight]` benchmark output or ink! weight annotation and compare to measured.

## Fix

- Use `Mapping`/`LookupMap`-style lazy storage for anything unbounded; keep `Vec`/`StorageVec` only for small, bounded sets.
- Bound iteration: take a page size, iterate a caller-supplied range, or maintain an index; never loop over a user-growable collection in one call.
- Declare weight for the worst case and benchmark it; add storage-deposit limits where users grow state.
- Gate `set_code_hash` behind owner/root authorization and, where possible, a timelock or governance check.
- Write explicit storage migrations for every layout change; verify field-by-field against the previous version.
- Keep field order stable and document the packing; test storage dumps across versions.

## Storage and weight quick reference

- `Mapping::get(k)` / `insert(k, v)` touch one slot; `Mapping` has no cheap `len()` or iteration.
- `StorageVec` push/pop are O(1); `iter()` and index access deserialize per element.
- FRAME weight comes from `#[pallet::weight(T::WeightInfo::call())]`; ink! functions may carry a weight annotation.
- Storage deposits are returned on delete; forgetting to clear state strands the deposit forever.

## Severity and finding bar

- An unguarded `set_code_hash` is **Critical** (full logic takeover).
- A layout-changing upgrade without a migration is **Critical** if it corrupts balances/owner, **High** otherwise.
- Unbounded iteration on a hot path is **High**; on a rarely used admin path, **Medium**.
- Weight under-declaration is **Medium** unless it enables a cheap DoS, then **High**.

## See also

- `ecosystems/substrate` — the ecosystem playbook.
- `vulnerabilities/dos-griefing`, `vulnerabilities/upgradeability-proxy` — the general classes.
- `substrate-dispatch-origin`, `ink-storage-and-abi` — sibling ink! surfaces.
