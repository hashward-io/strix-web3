---
name: near
description: NEAR playbook — Rust and AssemblyScript contracts; async promises, predecessor vs signer, storage staking, payable yoctoNEAR, unbounded iteration, near-workspaces
---

# NEAR Ecosystem

NEAR is sharded and **asynchronous**: a cross-contract call is a promise that resolves in a later block. Contracts are WASM with declarative state; the runtime charges **storage staking** (locked NEAR per byte) and gas. The distinctive bugs are **promise trust**, **`predecessor_account_id` vs `signer_account_id`**, and **attached deposit**.

## When to use

- A Rust contract (`near-sdk`) or an AssemblyScript contract (`near-sdk-as`).
- Code using `#[near_bindgen]`, promises, `env::predecessor_account_id`, storage collections, or `#[payable]`.
- You need the bug-class map before narrowing to `tooling/near`.

## Contract model

- `#[near_bindgen]` on a `struct` + `impl`; public methods are `pub fn`. State lives in the contract account's trie.
- **`#[init]`** constructs state; `#[init(ignore_state)]` accepts migration. Re-initialization is rejected by the SDK **unless** a plain public method writes initial state.
- Rust panics abort the call and refund unused gas; a panic in a callback leaves the promise chain half-done.
- `BorshStorageKey` prefixes collections; a wrong or duplicated prefix aliases two sub-tries.

## Identities and trust

- **`env::predecessor_account_id()`** — the immediate caller (may be a contract). **`env::signer_account_id()`** — the original tx signer. Authorizing on the wrong one is spoofable: any contract can call you as predecessor while a different account signed the tx.
- **`env::current_account_id()`** — you; verify callback/scheduler callers against it.
- **Attached deposit:** `env::attached_deposit()` (yoctoNEAR). **`#[payable]` is required to accept > 0**, else the call panics with `MethodMustBePayable`. A payable method must account for the deposit and refund excess.
- `env::account_balance()` vs `env::account_locked_balance()` (storage-locked); spending the total may strand funds.

## Storage and deposits

- **Storage staking:** the contract locks NEAR proportional to bytes stored (~1 NEAR per 100 KB). Growing storage without charging the caller **burns the contract's own balance** — a griefing vector (anyone can call and grow state).
- `StorageMap`/`LookupMap`/`Vector`/`UnorderedMap` from `near_sdk::collections`. Iterating `UnorderedMap::keys` is **unbounded** — a loop over all keys in one call runs out of gas.
- Deposit-refund patterns: collect, do work, refund the remainder; a missing refund locks user funds.

## Async promises

- **Promises** (`Promise::new(account).function_call(...).then(...)`) run later; the callback gets the result. The callback's `env::predecessor_account_id()` is the **contract**, not the user — carry the user id in a map keyed by a nonce/`current_account_id`.
- **Arbitrary callee:** `Promise::new(caller_supplied)` is an arbitrary cross-contract call unless validated.
- **Gas attached to a promise** must be provisioned; too little reverts the promise, too much wastes the user's gas.
- The callee can be malicious; validate every returned value.

## Access control and state

- Owner checks via `env::predecessor_account_id() == self.owner_id`; account ids are canonical, so string comparison is safe — a missing check is the hole.
- A panic rolls back the current receipt but not prior receipts in the async chain.
- There is no synchronous reentrancy, but a callback that assumes no state changed since the call is exploitable.

## Toolchain & build

- `cargo near build` (near-sdk 5) or `cargo build --target wasm32-unknown-unknown --release`; deploy the `.wasm`.
- **`near-workspaces`** (Rust and JS) run a sandbox node and drive multi-account, multi-block flows.
- `near-cli-rs` (`near`) for deploy/call; `cargo test` with `near-sdk` `testing_env!` unit tests.

## Where the bugs live

- **Promise/async cross-contract trust** — trusting a callback result or a caller-supplied callee; missing user-id correlation.
- **`predecessor_account_id` vs `signer_account_id`** — authorizing on the wrong identity.
- **Storage staking/deposit** — unbounded growth charged to the contract; missing refunds.
- **Unbounded iteration** — looping over all keys/values in one call.
- **`#[payable]` / yoctoNEAR** — missing `#[payable]` or unaccounted `attached_deposit`; the `1 yoctoNEAR` convention for security-critical calls.
- **Reinit / migration** — a public method that writes initial state; `#[init(ignore_state)]` without validation.
- **Callback gas** — under/over-provisioned gas; an unhandled failed promise.

## Proof standard

A `near-workspaces` test on a sandbox node driving the malicious flow across blocks (impersonate a signer/predecessor, trigger a callback, grow storage, exploit async ordering) and asserting the unauthorized effect. A `testing_env!` unit test covers local checks; async needs the sandbox. A trace without a test is a **lead**.

## Testing

- `near-workspaces` for sandbox tests with multiple accounts and promise resolution.
- `testing_env!` + `VMContextBuilder` for `predecessor_account_id`, `attached_deposit`, `block_height`.
- Test both signer and predecessor distinctions explicitly.
- Send > 0 deposit to a non-payable method and assert the panic.

## Fix patterns

Authorize on `predecessor_account_id` for direct calls and use `signer_account_id` only where the intent is the tx signer; require `#[payable]` deliberately and refund excess; charge a storage deposit and reject unbounded growth; bound all iteration (paginate); correlate async results to the expected user; verify callback callers; validate callee account ids; use `#[init(ignore_state)]` with migration validation; provision enough promise gas.
