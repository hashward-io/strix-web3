---
name: cosmwasm-message-and-reply
description: CosmWasm submessages and replies — Reply id collisions, error swallowing, sudo/migrate, WasmMsg::Execute targets, query trust, unbounded iteration DoS
---

# CosmWasm Messages and Replies

A CosmWasm contract is a message router. Every `SubMsg`, `Reply`, `sudo`, and cross-contract dispatch is an opportunity for a confused-id, a swallowed error, or an attacker-controlled target.

## Where to look

- **Submessage and `Reply` plumbing.** `SubMsg { id, msg, gas_limit, reply_on }` with `reply_on` in `Never | Success | Error | Always`, answered by `reply(deps, env, msg: Reply { id, result })`. The `id` you set is echoed back to *some* reply handler.
- **Reply id collisions.** If two different submessages share an `id` (including two call sites both using e.g. `1`), the `reply` handler cannot tell them apart and may apply the wrong follow-up state to the wrong operation. Enumerate all ids and confirm uniqueness per semantic action.
- **Reply id `0` reuse.** A default/undeclared id of `0` across unrelated submessages is a common collision; make each id a named constant.
- **Error swallowing.** `ReplyOn::Never` and handlers that ignore `SubMsgResult::Err(_)` (or map it to `Ok(Response::default())`) hide failed sends: the contract records success for an operation that never happened.
- **Swallowed query / conversion errors.** `let _ = deps.querier...`, `.ok()`, and `unwrap_or_default()` on a fallible call hide a failure that later logic assumes away.
- **Reply state assumptions.** Assuming a submessage succeeded, or that state written before it is rolled back on error. `ReplyOn::Never` does not revert the parent, and the reply runs in fresh execution where pre-submessage writes persist.
- **`sudo` entry point.** `sudo(deps, env, msg: SudoMsg)` is invoked by the chain's privileged module (governance/admin), never by users — but verify it still re-validates `msg` and does not accept spoofable fields. Any `sudo` branch that trusts an attacker-supplied identity is a finding.
- **`migrate` entry point.** Chain-enforced admin-gated, but the handler's own version checks and storage assumptions are the contract's responsibility (see `vulnerabilities/cosmwasm-migration-and-admin`).
- **`WasmMsg::Execute` to an attacker-controlled address.** A stored "target" contract address an attacker can set, then dispatched via `WasmMsg::Execute { contract_addr, msg, funds }`, lets them choose the callee and message.
- **`WasmMsg::Instantiate` with an attacker-chosen `code_id`.** Instantiating attacker code under your contract's identity or funds. Validate code ids against an allow-list.
- **`WasmMsg::Migrate` forwarding.** Relaying a migrate to a target the caller controls re-points another contract's state.
- **Query trust.** `deps.querier.query_wasm_smart::<T>(contract, &msg)` returns whatever the (possibly attacker-chosen) contract says. If `contract` is a parameter or a stored address the attacker can set, they control the answer — a price, a balance, an authorization.
- **Code-id / migration-version checks for queried contracts.** Even a fixed address can be a proxy whose code changed; `query_wasm_contract_info` can help pin it.
- **Unbounded `range` / iteration DoS.** `deps.storage.range(None, None, Order::Ascending)` over an unbounded map, or a loop loading unbounded entries, exhausts gas and bricks the entry point.
- **Unbounded state growth.** A `Vec` or map that only grows (users, ids, receivers) eventually makes loads/payments unaffordable.

## Attack plan

1. List every `add_submessage` / `SubMsg`; record `id`, `reply_on`, and the target message.
2. Detect id collisions and match each reply branch to its originating action.
3. For each reply, ask what happens on `Err` — is the error propagated, ignored, or turned into success?
4. Inventory `sudo` and cross-contract dispatch targets; trace where each address/code id comes from.
5. Find every `query_wasm_smart` whose `contract` is not a compile-time constant or validated address.
6. Look for `range` loops and any state that grows without bound.

## Proof

Use `cw-multitest` to deploy a malicious receiver that returns a chosen value from a smart query, fails a submessage, or returns the same reply `id`. Drive the collision, the swallowed error, or the poisoned query and show the resulting state (minted shares, released funds). For a DoS, populate the map and call the loop to show gas exhaustion.

## Fix

Give each submessage a unique, documented `id` and handle `SubMsgResult::Err` explicitly, propagating failure. Only expose `sudo`/`migrate` semantics the chain intends and re-validate payloads. Never dispatch to an address or instantiate a code id the caller can influence; validate and store them. Treat all cross-contract query results as untrusted unless the address is fixed. Bound every `range` loop and store aggregates instead of iterating.

## Variants and adjacent bugs

- **Reply id collision** — two submessages share an id.
- **Swallowed `Err`** — success recorded for a failed submessage.
- **Attacker dispatch/instantiate target** — a `WasmMsg` built from unvalidated input.
- **Poisoned smart query** — the queried contract is attacker-chosen.
- **Unbounded range/iteration** — a gas-exhaustion DoS.

## Do not flag

- Unique, documented reply ids with explicit error propagation.
- `sudo`/`migrate` reachable only through the chain's privileged path.
- Bounded loops over a capped set.

## Leads vs findings

- A shared reply id or an ignored error is a **lead** until the state effect is shown.
- Demonstrate the collision, poisoned query, or DoS with `cw-multitest`.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/cosmwasm` — submessage, reply, and sudo model.
- `tooling/cosmwasm` — `cw-multitest` and build commands.
- `vulnerabilities/cosmwasm-migration-and-admin` — entry-point authorization.
