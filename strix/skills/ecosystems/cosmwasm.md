---
name: cosmwasm
description: CosmWasm and Cosmos SDK playbook — entry points, DepsMut/MessageInfo, Addr canonicalization, submessage/reply, governance migration, CosmWasm bug-class map
---

# CosmWasm / Cosmos Ecosystem

CosmWasm contracts are Rust WASM modules called by the Cosmos SDK over JSON messages. A contract returns the messages it wants the chain to execute. The trust boundaries are **address canonicalization**, **attached funds**, and the **submessage/reply** state machine.

## When to use

- A CosmWasm contract (`src/contract.rs`, `Cargo.toml` with `cosmwasm-std`, `cw-*`).
- A Cosmos SDK module (Go) or a chain upgrade handler.
- You need the bug-class map before narrowing to `tooling/cw-multitest`.

## Entry points

- **`instantiate(deps, env, info, msg)`** — constructor; set admin and initial config. A fresh instance with a hostile config is possible if the code allows it.
- **`execute(deps, env, info, msg)`** — the dispatcher; `info.sender` is the caller, `info.funds` the attached coins.
- **`query(deps, env, msg)`** — read-only; a query that trusts `deps.querier` results is spoofable if the queried contract is not pinned.
- **`reply(deps, env, msg)`** — resumes a multi-step flow when a dispatched submessage resolves; selected by `msg.id`.
- **`migrate(deps, env, msg)`** — runs after an admin calls `MsgMigrateContract`; version-gate the migration.
- **`sudo(deps, env, msg)`** — called by the chain (never a user) for privileged operations (e.g. cw20/cw721 mint hooks).
- **Admin:** the admin can replace the code id entirely; an unchecked admin makes every invariant optional.

## Types and trust

- **`DepsMut` / `Deps`:** querier + storage; `deps.querier.query_wasm_smart(addr, msg)` runs arbitrary contracts — pin `addr`.
- **`Env`:** block height/time and the canonical contract address.
- **`MessageInfo`:** `sender: Addr` (canonical) and `funds: Vec<Coin>`.
- **`Addr` vs `String`:** `Addr` is validated and canonicalized; a raw `String` used for comparisons is spoofable.
- **Canonicalization:** bech32 prefixes differ per chain (`cosmos1…`, `osmo1…`, `juno1…`); `deps.api.addr_canonicalize`/`addr_humanize`. Comparing across representations (or across chain prefixes) is a bug.

## Funds and coins

- **`info.funds`** is the attached amount; a method that moves value must check it. Native funds and CW20 tokens are different value models.
- **`Uint128`** for token amounts (no floats/negatives); `Decimal`/`Decimal256` for ratios. `Uint128 * Decimal` is integer math — rounding direction matters.
- Watch zero-amount coins, duplicate denoms in `funds`, and denom checks that use the wrong string.
- `Uint128` addition can overflow (panic); use `checked_*` and pick a policy.

## Submessages and replies

- A submessage (`CosmosMsg::Wasm(WasmMsg::Execute{…})`) is dispatched after the current call returns. By default a failed submessage reverts the whole tx; `ReplyOn::Error`/`Success`/`Always` change that.
- **`reply`** selects by `msg.id`; a handler that trusts the reply payload without validating the state it recorded is trickable by a re-ordered or duplicated submessage.
- With `ReplyOn::Error` the reply receives the error, not success data.

## Governance and migration

- **`migrate`** is admin-only and originates from governance or an admin. Validate `msg` against the expected version to avoid a storage reshape.
- **`sudo`** is privileged; a `sudo` entry point that mints or burns must be exactly the bridge/minter.
- **Chain upgrades** (Cosmos SDK `x/upgrade`) run module migration handlers; a module that skips one leaves old state.

## Toolchain & build

- `cargo build --target wasm32-unknown-unknown --release` (or `cargo wasm`); `cosmwasm-check contract.wasm` gates validity/features.
- **`cw-multitest`** for multi-contract integration tests; `cosmwasm-std`'s `mock_dependencies`, `mock_dependencies_with_balances`, `mock_info` for unit tests.
- `cargo test`, `cargo clippy`.

## Where the bugs live

- **Address canonicalization** — bech32 vs `Addr` vs `String`; cross-chain prefix confusion.
- **Funds (`info.funds`)** — not checking attached denom/amount; assuming CW20 equals native.
- **Reply/submessage & `sudo`** — reply-id collision; unvalidated payload; a `sudo`/`migrate` reachable by the wrong authority.
- **Migration/admin** — missing version gate; admin set to an EOA or left as `None` where one was required.
- **Unbounded iteration** — walking all accounts/keys in an `execute`; gas/DoS.
- **Decimal `Uint128`** — rounding, truncation, multiply order.
- **Querier trust** — `query_wasm_smart` to an attacker-chosen address.

## Proof standard

A `cw-multitest` (or `mock_dependencies`) test reproducing the exploit: wrong `info.sender`, spoofed attached funds, a crafted submessage/reply sequence, or a bad migration, asserting the unauthorized state change. A code trace is a **lead**.

## Testing

- `cw-multitest` for multi-contract flows (instantiate → execute → query → reply) with balances.
- `mock_dependencies`/`mock_info` for unit-level sender and funds control.
- `cosmwasm-check` to catch invalid Wasm/feature flags before deploy.
- Query state after each message to confirm the effect.

## Fix patterns

Compare canonical `Addr`s; check `info.funds` for denom and exact/at-least amount; validate `reply.id` and its payload; version-gate `migrate`; restrict `sudo`; bound iteration or paginate; use `checked_*` on `Uint128`; pin querier addresses; validate the admin on instantiate and reject zero/`None`.
