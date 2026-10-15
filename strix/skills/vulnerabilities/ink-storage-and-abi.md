---
name: ink-storage-and-abi
description: ink! ABI and storage — selector collisions, constructor re-init, trait_definition vs trait impl, cross-contract invoke trust and reentrancy, and transfer/value handling
---

# ink! Storage and ABI

The ink! ABI is a set of 4-byte selectors derived from message names, and storage is a flat set of slots. Selector collisions route a call to the wrong message, bare-name traits confuse dispatch, and cross-contract `invoke` calls hand control to code you do not control.

## Where to look

- Selectors: `#[ink(message)]` methods and `#[ink(selector = 0xXXXXXXXX)]` overrides. Default selectors are derived from the message name (and trait path).
- Constructors: `#[ink(constructor)]` and any public `#[ink(message)]` named like an initializer. A constructor runs only at instantiation; a *message* named `init`/`initialize` can be called repeatedly.
- Traits: `#[ink::trait_definition]` (a callable interface for cross-contract calls) versus `#[ink(impl)]`/`#[ink::trait_impl]` on an implementation block. Mixing them, or forgetting `#[ink(impl)]`, changes which methods are dispatched.
- Cross-contract: `build_call::<Env>().call_flags(CallFlags::...)`, `invoke_contract`, and the return `Result`. Reentrancy is not blocked by default.
- Value: `self.env().transferred_value()`, `self.env().transfer(dest, value)` (returns `Result`), and `#[ink(payable)]`.

## Attack plan

1. Enumerate every selector. Two messages can collide if one uses an explicit `#[ink(selector = ...)]` that equals another's derived selector, or if names/trait paths hash to the same 4 bytes. A collision sends the wrong call to the wrong handler.
2. Constructor re-init: find a public `#[ink(message)]` that sets owner/config. If it is not guarded (can be called twice, or after `set_code_hash`), an attacker re-initializes the contract (paired with `substrate-dispatch-origin`).
3. Trait confusion: a `trait_definition` block accidentally marked `#[ink(impl)]`, or a default trait method that is externally reachable and skips the guard the concrete method has. Check which methods the ABI actually exposes.
4. Cross-contract invoke trust: a call to another contract that returns data used as an authority signal (e.g. "balanceOf said yes"). The callee is arbitrary if its address is attacker-influenced. Verify the callee address is expected.
5. Reentrancy via invoke: if the contract updates state *after* `invoke_contract`, the callee can re-enter a message that reads the stale state. ink! has no `nonReentrant` by default — implement a lock.
6. Value handling: `self.env().transfer` returning `Err` while the code ignores it strands or misroutes funds; a `payable` message that accepts value but never credits it; comparing `transferred_value()` to a stored price that the caller controls.
7. ABI compatibility across upgrades: after `set_code_hash`, a selector that now maps to a different message is a silent behavior change for integrations.

## Proof

- `cargo contract test` with `ink::env::test::set_caller` / `set_value_transferred`; assert a colliding selector or an unguarded re-init succeeds.
- `cargo contract build` then inspect the metadata JSON (or `cargo contract` output) for duplicate selectors.
- For reentrancy, a two-contract e2e (`ink_e2e`) where the callee re-enters and reads stale state; show the divergent value.
- For value, use `set_value_transferred` and assert funds are stuck.

## Fix

- Avoid explicit selector overrides unless necessary; if used, verify uniqueness against every other message in the ABI.
- Make initialization constructor-only; guard any post-deploy re-initialization behind owner + a one-time flag.
- Use `#[ink::trait_definition]` for interfaces and `#[ink(impl)]` / `#[ink::trait_impl]` consistently; verify the exposed ABI.
- Validate cross-contract callee addresses against expected values; treat returned data as untrusted.
- Add an explicit reentrancy guard around any message that makes a cross-contract call and mutates shared state.
- Always handle the `Result` from `transfer`; credit `transferred_value()` explicitly in payable messages.

## ABI and value quick reference

- Default selectors derive from the message name; `#[ink(selector = 0xdeadbeef)]` overrides them.
- `#[ink::trait_definition]` generates a callable interface; `#[ink(impl)]` / `#[ink::trait_impl]` mark implementations.
- `self.env().transfer(dest, value) -> Result<(), ink::env::Error>` — always handle the result.
- `self.env().transferred_value() -> Balance` is what this message received.
- Cross-contract `build_call::<Env>().call(...)` / `invoke_contract`; `CallFlags::ALLOW_REENTRY` is opt-in.

## Severity and finding bar

- A selector collision that routes to the wrong handler is **High**, **Critical** if it bypasses a guard.
- An unguarded re-initialization is **Critical**.
- Ignored `transfer` errors that strand funds are **High** if value is lost, **Medium** otherwise.

## See also

- `ecosystems/substrate` — the ecosystem playbook.
- `vulnerabilities/reentrancy`, `vulnerabilities/access-control` — the general classes.
- `substrate-dispatch-origin`, `substrate-storage-and-weight` — sibling ink! surfaces.
