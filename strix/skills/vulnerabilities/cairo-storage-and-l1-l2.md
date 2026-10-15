---
name: cairo-storage-and-l1-l2
description: Cairo/Starknet storage and L1-L2 — LegacyMap vs Map collisions, base addresses, components, l1_handler caller checks, class_hash/address confusion
---

# Cairo Storage and L1-L2 Messaging

Starknet storage is not "slots" you can reason about byte-for-byte; a variable's address is derived by hashing. Every derivation is a place where two logical keys can alias, and every L1-L2 message is a place where the sender must be authenticated.

## Where to look

- **`LegacyMap` vs `Map`.** `LegacyMap<K, V>` requires `K: LegacyHash` and derives the address from `hash(K)`; structurally different keys can alias, and tuple/struct keys are unsafe. `Map<K, V>` requires `K: Hash` and computes the address from the storage variable's `storage_base_address` plus `hash(key)`. Grep both names.
- **Mixed map types for one logical field.** A variable migrated `LegacyMap` → `Map` (or declared with a different key type) resolves to a different address, orphaning old entries or aliasing new ones onto stale data.
- **`storage_base_address`.** `starknet::storage_access::storage_base_address_from_felt252`, `.storage_base_address()`, and `Map::entry(key).storage_address()`. A hand-assigned base (`@some_address`) that collides with another variable aliases storage.
- **`#[starknet::storage_node]`.** Derive macros give each nested field a derived address; a struct nested at two different bases is fine, but a manually managed pointer that overlaps is not. Inspect `Map<K, #[starknet::storage_node] Nested>` layouts.
- **Component storage.** The `component!` macro allocates each component's storage at a base derived from its name, exposed through `HasComponent`. Two components with colliding names, or a component re-instantiated at a hand-picked base, can overlap.
- **`Map` key collisions.** Even with `Map`, a key that is a hash of attacker-influenced fields can be made to equal another key's hash. For `Map<felt252, _>`, check where the key comes from.
- **`send_message_to_l1_syscall`.** `send_message_to_l1_syscall(to_address: felt252, payload: Span<felt252>)` is fire-and-forget. The payload is interpreted by the L1 consumer; check `to_address` and payload are trusted and that the L1 side re-authenticates the L2 sender.
- **`#[l1_handler]` caller validation (top finding here).** `#[l1_handler] fn handler(from_address: felt252, ...)` may only be invoked by the sequencer from an L1→L2 message — but **anyone on L1 can originate** a message through the core contract. If the handler does not assert `from_address == EXPECTED_L1_CONTRACT`, an attacker on L1 drives arbitrary L2 state.
- **`#[l1_handler]` payload and selector.** Check length validation and that `to_address`/selector assumptions hold; a handler that trusts the payload shape can be fed a malformed one.
- **`class_hash` vs `contract_address` confusion.** `library_call_syscall` and `replace_class_syscall` take a **class hash**; `call_contract_syscall` takes a **contract address**. Both are `felt252` at the type level, so swapping them compiles cleanly.
- **Dispatchers fed the wrong identifier.** `IFooDispatcher { contract_address }` takes an address; passing a class hash executes the wrong target. Look for raw `felt252` params named `class_hash` / `address`.
- **`deploy_syscall`.** Returns `(contract_address, class_hash)`; a caller that stores the wrong element in an "owner" or "registry" field creates a spoofable identity.
- **`get_caller_address()` vs `get_contract_address()`.** Caller is the immediate caller (an attacker contract, or the L1-handler relayer); contract is self, so using it for authorization is meaningless. `get_tx_info().account_contract_address` differs from both.
- **`get_sequencer_address` / `get_block_hash`.** OS-provided; do not treat as a trusted identity or a cryptographic commitment without validation.

## Attack plan

1. Map every storage variable to its type and derived address; flag `LegacyMap`, hand-set bases, and any type migration.
2. For each `Map`/`LegacyMap`, ask whether an attacker-controlled key can alias another key's entry.
3. Enumerate every `#[l1_handler]`; verify each binds `from_address` to the trusted L1 contract and validates payload length.
4. For every syscall, confirm the argument is the right kind of identifier (class hash vs address) and was not passed in unvalidated.
5. Check identity guards: does authorization use `get_caller_address()`, or accidentally `get_contract_address()` / tx-info fields?
6. Trace `send_message_to_l1`: what does the L1 consumer do with the payload, and can it be spoofed?

## Proof

Use `snforge` with `starknet::testing::{set_caller_address, set_contract_address}` to replay the wrong caller. For an `l1_handler`, call it through the test harness with an attacker-controlled `from_address` and show the state change. For storage aliasing, write through one key and read another, or migrate a variable and show the corrupted read. For class/address confusion, show `library_call` executing an attacker class. File it only with the trace; otherwise it is a lead.

## Fix

Prefer `Map` over `LegacyMap` and never migrate a live variable without an explicit migration. Bind `#[l1_handler]` to a constant, validated L1 sender and validate payloads. Keep `ContractAddress` typed (`core::starknet::contract_address::ContractAddress`) instead of raw `felt252`, and never pass a class hash where an address is expected. Use `get_caller_address()` for all authorization.

## Variants and adjacent bugs

- **`LegacyMap` key aliasing** — two keys hashing to the same derived address.
- **Mixed map types** — a field read as `Map` after being written as `LegacyMap`.
- **Unbound `#[l1_handler]`** — missing `from_address` check; an attacker originates on L1.
- **class_hash/address swap** — `library_call` given an address, or `call_contract` given a class hash.
- **Self-identity guard** — authorization using `get_contract_address()`.

## Do not flag

- Storage addresses derived automatically by `Map`/`storage_node` with no manual base.
- `#[l1_handler]`s that bind a constant L1 sender and validate payload length.
- `send_message_to_l1` payloads whose L1 consumer re-authenticates the L2 sender.

## Leads vs findings

- A `LegacyMap` or a missing `from_address` check is a **lead** until exploited.
- Show the aliased read or the attacker-originated call via `starknet::testing`.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/cairo` — platform model and storage semantics.
- `tooling/cairo-scarb` — build and test commands.
- `vulnerabilities/cairo-access-and-upgrade` — guards and upgrade paths.
