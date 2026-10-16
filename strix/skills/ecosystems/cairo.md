---
name: cairo
description: Cairo 1 / Starknet playbook — felt252 vs u256/i128, storage addressing, class_hash upgrades, L1-L2 messaging, and the Cairo bug-class map
---

# Cairo / Starknet Ecosystem

Cairo 1 (Cairo 2.x) compiles to Sierra, then CASM, and runs on Starknet's Cairo VM. Its field element (`felt252`) is prime-field arithmetic; integers are separate types. The persistent surprises are **felt arithmetic**, **storage address derivation**, and **L1↔L2 message trust**.

## When to use

- A Starknet contract (`#[starknet::contract]`, `Scarb.toml`) in Cairo 1/2 (not legacy Cairo 0).
- Code with `felt252`, `u256`, `i128`, storage maps, `class_hash`, or `#[l1_handler]`.
- You need the bug-class map before narrowing to `tooling/cairo-scarb`.

## Language surfaces

- **`felt252`:** a field element modulo the STARK prime (~2^251). Arithmetic wraps mod p — `felt252` overflow does **not** revert, so never hold a balance in `felt252`.
- **`u256`, `i128`, `u64`, `u32`, `u16`, `u8`:** checked arithmetic (overflow panics) outside `unchecked`/wrapping methods. Conversions via `Into`/`TryInto`; a `felt252` → `u256` cast can truncate or panic depending on the API.
- **Division by zero** panics for integers; for `felt252`, `0` has no inverse — check `div_rem` behavior.
- **Serialization:** `#[derive(Serde)]` field order defines the calldata/ABI layout; a mismatch reverts.
- **`Option`/`Result`** `.unwrap()` on attacker input is a DoS.

## Storage

- Storage variables are declared in a `#[storage]` struct; each address is derived from a snapshot of the struct. **Inserting or reordering a variable in an upgrade changes the address of later variables** — a storage-layout break.
- **`LegacyMap` vs `Map`:** `LegacyMap` hashes keys against the base address; `Map` (newer) is the recommended type. A non-unique key aliases an entry.
- Reading an unset slot returns `0`; a `bool`/enum encoded as `0` can look like a valid default.

## Contract structure and upgrades

- `#[starknet::contract] mod X` with `#[external(v0)]`, `#[constructor]`, `#[l1_handler]`, and a `#[generate_trait]` impl.
- **Upgrade:** `replace_class_syscall(new_class_hash)` swaps the class behind an address; storage persists, so the new class's layout must be compatible. There are no automatic storage gaps — verify offsets.
- **`class_hash` vs `contract_address`:** distinct. A registry keyed on the wrong one is spoofable when class hashes are reused.
- **`__validate__` / `__execute__`:** account-abstraction entry points; a hand-rolled account must validate the tx correctly (nonce, signature, and that the caller is the protocol).

## L1↔L2 messaging

- **L2→L1:** `send_message_to_l1_syscall`; consumed on Ethereum by the Starknet Core contract with the L2 sender as `from_address`.
- **L1→L2:** `#[l1_handler] fn ...(from_address: felt252, ...)`. **`from_address` is attacker-controllable if the L1 contract lets anyone send** — always check `from_address == expected_l1_contract`, and that the L1 sender was authorized. This is the Cairo equivalent of a `msg.sender` trust gap.
- L1→L2 messages can be cancelled; do not assume unconditional delivery.

## Syscalls, oracles, and hints

- `get_caller_address()`, `get_contract_address()`, `get_block_info()`, `get_tx_info()`, `get_block_hash()`.
- `get_block_hash` is valid only for the last ~10 blocks and is predictable — not a randomness source.
- `starknet::info` exposes `tx_info` (version, nonce, `account_contract_address`); validate anything you trust from it.

## Toolchain & build

- **Scarb** (`Scarb.toml`): `scarb build`, `scarb test`, `scarb cairo-test`.
- **Starknet Foundry / snforge:** `snforge test`; cheatcodes `start_cheat_caller_address`, `start_cheat_block_timestamp`, `mock_call`.
- **`sncast`** for deploy/calls; `starkli` as an alternative.
- Static analysis: `caracal` (Cairo static analyzer), `amarna` (legacy), `cairo-lint` (compiler-integrated).

## Where the bugs live

- **`felt252` overflow / division** — arithmetic wraps mod p; a `felt252` balance or counter.
- **`u256`/`i128` conversions** — truncating `as` casts; `felt252` ↔ `u256`.
- **Storage address collisions & legacy maps** — reordering storage across an upgrade; non-unique keys.
- **L1↔L2 message trust** — unvalidated `from_address` in `#[l1_handler]`; assuming delivery.
- **Upgrade / `class_hash`** — incompatible storage layout; wrong registry key.
- **Hints / oracles** — `get_block_hash` for randomness; trusting `tx_info` fields.
- **Access control with `ContractAddress`** — comparing `get_caller_address()` to a stored address; a zero-address default; account-abstraction validation gaps.
- **Integer panic DoS** — division by zero, `unwrap` on external input.

## Proof standard

A `snforge` test with cheatcodes that impersonates the attacker caller (or a crafted L1 handler) and asserts the unauthorized state change or drained balance. For L1↔L2, show the forged `from_address` reaching the handler. A trace without a passing test is a **lead**.

## Testing

- `snforge test` with `start_cheat_caller_address`, `start_cheat_contract_address`, `start_cheat_block_timestamp`.
- Fork tests against live Starknet where `snforge` fork config is available.
- `caracal detect` for a static lead pass; confirm by hand.
- Fuzz arithmetic paths with boundary inputs.

## Fix patterns

Use `u256`/`u128` for all value math; explicit `TryInto` with handling over `as`; keep storage layouts append-only across upgrades; validate `from_address` in every `#[l1_handler]`; never use `get_block_hash` for randomness; gate admin entry points on `get_caller_address`; avoid `unwrap` on external input.
