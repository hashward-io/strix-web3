---
name: substrate
description: ink! and Substrate FRAME pallet playbook — dispatchables, origin/ensure_signed, payable, storage layout, Weight, cross-contract calls, PSP22/PSP34
---

# Substrate / ink! Ecosystem

A Substrate chain is Rust: FRAME **pallets** (runtime modules) and **ink!** smart contracts both compile to WASM. They share one authority model, **`origin`**, and one failure mode: a dispatchable that trusts its origin or forgets to charge `Weight`.

## When to use

- An ink! contract (`#[ink::contract]`, `Cargo.toml` with `ink`), a PSP22/PSP34 token, or code using `call`/`delegate`.
- A FRAME pallet (`#[pallet::call]`, `#[pallet::storage]`) or a runtime upgrade.
- You need the bug-class map before narrowing to `tooling/substrate`.

## ink! contracts

- `#[ink::contract] mod X` with `#[ink(storage)]`, `#[ink(constructor)]`, `#[ink(message)]`.
- **Every `#[ink(message)]` is externally callable;** a state-mutating message with no origin check is an access-control hole.
- `self.env().caller()` is the immediate caller (like `msg.sender`); `self.env().transferred_value()` is the attached value for a `#[ink(message, payable)]`.
- **`#[ink(payable)]`:** a non-payable message rejects attached value; a payable one must account for `transferred_value`.
- The constructor runs once at instantiation; with `delegate`/upgrade, storage persists — verify the layout.
- Trait definitions (`#[ink::trait_definition]`) and default methods: watch for interface drift.

## FRAME pallets

- `#[pallet::call]` dispatchables take `origin: OriginFor<T>`; **`ensure_signed(origin)?` (or `ensure_root`/`ensure_none`) is mandatory.** A dispatchable that uses the origin without `ensure_*` accepts any caller.
- `ensure_signed` returns the converted `T::AccountId`; `ensure_root` is for governance.
- The `Config` trait declares associated types; a pallet that trusts a `Config::…` type (e.g. a price) inherits its trust.
- **`#[pallet::storage]`** with `StorageValue`/`StorageMap`/`StorageDoubleMap`; `#[pallet::genesis_config]` for genesis.
- **`#[pallet::hooks]`** (`on_initialize`/`on_finalize`) run every block; a panic there halts the block or chain.
- `#[pallet::weight]` must bound the worst case; `#[pallet::compact]` changes SCALE encoding (a decoding mismatch).

## Storage layout and upgrades

- Storage keys derive from the pallet name + storage prefix; **renaming a pallet or reordering fields silently repoints storage**. Use explicit prefixes and `on_runtime_upgrade` migrations.
- **ink! storage** is laid out contiguously; changing field order across a `delegate`/upgrade corrupts data. There are no automatic storage gaps.
- ink! `Mapping<K, V>` is a hash map in contract storage; a non-unique key aliases entries.

## Weight and fees

- **`Weight`** (ref time + proof size) meters computation. A dispatchable must declare a bounded weight; unbounded iteration exceeds it and invalidates the block (a DoS).
- `transferred_value()` is the attached native balance; refund promised excess.
- **`StorageDeposit`** for ink! storage growth; letting anyone grow storage without a deposit is a griefing vector.

## Cross-contract calls and reentrancy

- ink! `self.env().call(...)` / `CallBuilder` calls another contract; `delegate` runs the callee with **the caller's storage and address** — a delegate to an attacker contract is catastrophic.
- **Reentrancy:** ink! permits re-entrant calls unless guarded; apply checks-effects-interactions and `openbrush`'s `ReentrancyGuard`.
- **`set_code`/`set_code_hash`:** upgrades; validate the caller (owner + `ensure_signed`) and the new code hash.

## Tokens: PSP22 / PSP34

- `openbrush`'s `PSP22` (ERC-20) and `PSP34` (ERC-721) traits. Audit the allowance flow, `transfer_from`, mint/burn authority, and metadata immutability.
- **`PSP22::transfer` returns `Result`** — ignoring it loses funds silently.
- **`PSP34` `approve`/`transfer`** is per-token; a wrong token-id check grants the wrong asset.

## Toolchain & build

- `cargo contract build` (→ `.contract` bundle), `cargo contract test`, `cargo contract call`.
- **Redspot** (Hardhat-like) and **e2e** tests (`ink::env::test`, `ink_e2e`) against a node.
- FRAME: `cargo build -p node-runtime`, `cargo test -p pallet-x`; `try-runtime on-runtime-upgrade` for migrations.

## Where the bugs live

- **Origin / `ensure_signed` misuse** — a dispatchable without `ensure_*`; the converted origin discarded; a reachable `ensure_root`.
- **Unguarded dispatchables** — a state-mutating `#[ink(message)]`/`#[pallet::call]` with no caller check.
- **Storage layout & packing** — field reorder/mispacking across an upgrade; non-unique map keys; missing migration.
- **`Weight` accounting** — unbounded loops, missing weight bounds, or understated weight.
- **`#[payable]`** — a payable message that ignores `transferred_value`; a non-payable message relied on to receive value.
- **Contract→contract reentrancy** — a `call` before a state update; `delegate` to an untrusted target.
- **Token/allowance** — PSP22 allowance race; PSP34 token-id confusion.

## Proof standard

A `cargo test` (ink! `#[ink::test]` with `ink::env::test::default_accounts`) or a Redspot/e2e test that calls the dispatchable with the wrong origin and asserts the unauthorized effect. For FRAME, a `mock` runtime (`new_test_ext`) driving the extrinsic from a non-owner origin; for migrations, `try-runtime`. An unbacked trace is a **lead**.

## Testing

- ink!: `#[ink::test]` + `ink::env::test::set_caller`; `ink_e2e` against a local node.
- FRAME: the `mock.rs` test runtime with `new_test_ext()`, `RuntimeOrigin::signed(...)`/`RuntimeOrigin::root()`.
- `try-runtime on-runtime-upgrade` for storage migrations.
- Fuzz weight/deposit paths with unbounded inputs.

## Fix patterns

`ensure_signed`/`ensure_root` on every dispatchable and use the returned account; gate owner-only messages on a stored owner checked via `self.env().caller()`; add `ReentrancyGuard`; declare honest weights and bound iteration; charge `StorageDeposit`; write storage migrations for layout changes; validate `set_code_hash` callers; use audited `openbrush` traits.
