---
name: sway
description: Sway / Fuel playbook — StorageMap and storage slots, predicates, scripts, AssetId, msg_sender, overflow modes, reentrancy, forc and fuel-core
---

# Sway / Fuel Ecosystem

Sway is Rust-like and compiles to FuelVM bytecode. Fuel differs from the EVM in three ways that create bugs: **native multi-asset** (`AssetId`), **predicates** (stateless authorizers), and **arithmetic overflow modes** set by compiler flags.

## When to use

- A Sway contract (`#[contract]`, `Forc.toml`), a predicate (`#[predicate]`), or a script (`#[script]`).
- Code using `StorageMap`, `AssetId`, `msg_sender`, `tx_id`, or external contract calls.
- You need the bug-class map before narrowing to `tooling/sway`.

## Program kinds

- **Contracts (`#[contract]`):** stateful ABI with storage; entry points are `#[storage(read)]`/`#[storage(write)]` and `#[payable]`.
- **Predicates (`#[predicate]`):** stateless, no storage, no ABI calls; they authorize spending an input by returning `bool`. Predicates are pure — a predicate that needs state cannot be a predicate.
- **Scripts (`#[script]`):** one-shot; may call contracts; no persistent state.

## Storage and state

- A `storage { }` block with `StorageMap<K, V>`, `StorageVec`, and scalar slots. `storage.x.read()`, `.write(v)`, `StorageMap::get(k).read()`.
- **`StorageMap::get` returns an `Option`/storage key;** reading an unset key yields the type's default — a `bool`/enum default can look valid.
- **A non-unique key aliases an entry.** `#[storage(read)]`/`#[storage(write)]` are enforced at compile time, but manual/legacy slots can collide.

## Assets and sender

- **`AssetId`** identifies a native asset; `AssetId::default()`/`base` is ETH. A function taking a contract `AssetId` parameter must validate it against the expected asset.
- **`msg_sender()`** returns the caller as an `Identity` (`Address` vs `ContractId`). Comparing an `Address` to a `ContractId` never matches — a type-confusion bug.
- **`msg_amount()`** is attached base asset (requires `#[payable]`); `this_balance(asset)`/`balance_of` is a per-asset balance. Confusing the two is a bug.
- **`caller_contract_id()`/`caller_address()`** is the immediate caller; distinguish it from `msg_sender`.

## Arithmetic

- **Overflow mode:** by default Sway **wraps**; build with `--error-on-overflow` to make arithmetic checked. Know which mode the deployment used — a wrapping build overflows silently.
- `u8..u256`; explicit `as` casts truncate. `checked_add`/`checked_mul` return `Option`.
- Division by zero reverts; fixed-point/log math is a precision surface.

## External calls and reentrancy

- `abi(MyContract, contract_id)` calls another contract; `contract_id` must be checked — an attacker-supplied contract id is an arbitrary call.
- **Reentrancy:** an external call can re-enter; there is no built-in guard (the `reentrancy` library adds one). Update state before calling out.
- Distinguish `msg_sender()` (identity) from `caller_contract_id()` (the actual calling contract).

## Toolchain & build

- `forc build` (with `--error-on-overflow` as appropriate), `forc test`, `forc fmt`, `forc doc`.
- `fuel-core run` for a local node; `forc deploy`/`forc run`; the `fuels` TypeScript SDK for integration tests; `forc-client` for scripts.
- `sway-lsp` for tooling.

## Where the bugs live

- **Storage `read/write` in predicates** — predicates are stateless; a design that needs state cannot be a predicate.
- **`msg_sender`/`AssetId` checks** — missing asset validation; `Address` vs `ContractId` mismatch; trusting a caller-supplied asset.
- **Arithmetic overflow (flag vs wrap)** — a default wrapping build; unchecked `as` casts.
- **Reentrancy via external calls** — state updated after a cross-contract call.
- **Asset-id confusion** — crediting the wrong asset; `AssetId::default()` vs a token contract id.
- **Predicate trust** — a predicate that returns `true` too broadly, or checks a field the spender controls.
- **Manual slot collisions** — two storage values sharing a slot.

## Proof standard

A `forc test` (Rust `#[test]`) or a `fuels` TS integration test against `fuel-core` that exercises the malicious call (wrong sender, spoofed asset, reentrancy callback, overflow) and asserts the unauthorized transfer or state change, showing per-`AssetId` balances before and after. A code trace is a **lead**.

## Testing

- `forc test` for unit tests; `fuels`/`fuel-core` for end-to-end contract and script execution.
- Test overflow under the exact build flags used in deployment.
- Test predicates with crafted inputs that should be rejected.
- Reentrancy: deploy an attacker contract that re-enters.

## Fix patterns

Validate `AssetId` against a stored/expected id; compare `Identity` variants correctly; build with `--error-on-overflow` and use `checked_*`; update state before external calls and add a reentrancy guard; keep predicates stateless over controlled fields; use unique `StorageMap` keys; check `contract_id` before every ABI call; require `#[payable]` intentionally.
