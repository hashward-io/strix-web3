---
name: near-promise-and-storage
description: NEAR promises and storage — async cross-contract trust, callback validation, storage staking and #[payable], storage_usage DoS, unbounded iteration, and collection misuse
---

# NEAR Promises and Storage

NEAR contracts are async: a call returns before its cross-contract promises resolve, and results arrive at a *callback* method that anyone can invoke. Storage is staked and paid for, so unbounded growth is both a cost and an attack.

## Where to look

- Cross-contract calls: `Promise::new(account).function_call(method, args, deposit, gas)` and `.then(Promise::new(env::current_account_id()).function_call("callback", ...))`.
- Callbacks: the `callback` method and its validation of `env::predecessor_account_id()` (must equal the expected promise account) and `env::current_account_id()`.
- Result handling: `#[callback_result]` / `#[callback]` / `PromiseResult` — a returned `Value` treated as authoritative.
- Deposits: `#[payable]` methods and `env::attached_deposit()`; storage staking accounting via `env::storage_usage()` and the `StorageUsage` delta.
- Collections: `HashMap`, `LookupMap`, `UnorderedMap`, `TreeMap`, `Vector` from `near_sdk::collections`.
- Iteration: loops over keys/values in a method reachable by anyone.

## Attack plan

1. Callback trust: a callback validates neither `predecessor_account_id()` nor that a promise is outstanding. An attacker calls the callback method directly with fabricated arguments and injects a fake cross-contract result (e.g. "transfer succeeded", "price = 1").
2. Argument/return confusion: the callback parses an untrusted `Value` (JSON) into a struct and acts on it without checking the result variant. A `PromiseError` or a malicious payload is treated as success.
3. Out-of-order promises: two promises whose callbacks both mutate shared state; the callback does not correlate results to the originating request (no request id). Interleaving produces double-crediting.
4. Storage staking: a method that grows storage without requiring a matching `attached_deposit()` lets anyone consume the contract's NEAR balance (which is staked against storage) and eventually lock it or make writes fail.
5. `#[payable]` gaps: a fund-crediting path without `#[payable]` rejects the deposit (no-op or panic); a payable path that ignores `attached_deposit()` and credits a hard-coded amount.
6. `storage_usage` growth DoS: an unbounded collection (a `Vector`/`UnorderedMap` that any caller can push to) makes any function that iterates it exceed the gas limit — permanent DoS.
7. Collection misuse: `HashMap` fully deserializes on load (O(n) cost); using it for unbounded data is a gas bomb. `LookupMap` is lazy but has no iteration; code that needs to iterate a `LookupMap` cannot, hinting at a design mismatch.

## Proof

- `near-workspaces` integration test: create a sandbox, deploy the contract, call the callback directly with spoofed args and assert the injected state.
- Or `near-sdk` unit tests with `VMContextBuilder` to set `predecessor_account_id` and `attached_deposit`, then assert the unguarded credit.
- For storage DoS, push entries until an iterate method exceeds the gas limit (or the storage-staking balance).
- Show the exact `PromiseResult` handling that was bypassed.

## Fix

- Validate callbacks: `assert_eq!(env::predecessor_account_id(), env::current_account_id())` (or the expected promise account), correlate via a stored request id, and check the `PromiseResult` variant.
- Never act on a promise result without confirming a matching outstanding request.
- Require `#[payable]` and `attached_deposit()` on every storage-growing path; enforce `env::storage_usage()` accounting against the deposit.
- Bound every iteration: paginate, cap keys, or keep indexes; keep collections small.
- Use `LookupMap` for lazy single-key access and `UnorderedMap`/`TreeMap` only with a bounded, paginated iteration strategy; avoid `HashMap` for unbounded data.
- Refund excess deposit and handle failures explicitly.

## Promise quick reference

- `Promise::new(acct).function_call(method, args, deposit, gas)` returns a `Promise`; `.then(...)` chains a callback.
- A callback runs with `predecessor_account_id()` equal to the account that returned the promise, normally `current_account_id()`.
- `#[callback_result]` / `#[callback]` bind the previous promise's result; `PromiseResult` is `Successful(Value)` or `Failed`.
- `env::storage_usage()` returns bytes used; storage is staked from the contract's NEAR balance.
- `#[payable]` is required for a method to accept `attached_deposit`.

## Severity and finding bar

- A callback that trusts an unvalidated result is **Critical** when it credits funds.
- A directly callable callback that injects state is **High** to **Critical**.
- Storage-staking/growth DoS is **High** if it locks funds, **Medium** otherwise.
- Unbounded iteration is **High** on a user path, **Medium** on an admin path.

## See also

- `ecosystems/near` — the ecosystem playbook.
- `vulnerabilities/cross-contract-consistency`, `vulnerabilities/dos-griefing` — the general classes.
- `near-access-and-math` — the sibling NEAR surface.
