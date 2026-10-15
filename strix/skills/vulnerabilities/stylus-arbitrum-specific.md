---
name: stylus-arbitrum-specific
description: Arbitrum Stylus (Rust to WASM on the EVM) — entrypoint, sol_storage layout vs EVM slots, msg sender/value, call reentrancy, ink gas metering, panics, and ABI selectors
---

# Arbitrum Stylus Specifics

Stylus runs Rust compiled to WASM on Arbitrum Nitro, alongside the EVM. It speaks the Solidity ABI and can share storage slots with Solidity contracts, so the bugs sit at the seam: storage-layout compatibility, cross-language ABI selectors, Rust panics, and unguarded cross-contract calls.

## Where to look

- Entry point: `#[entrypoint]` on the storage struct, and the generated `user_entrypoint` / exported methods.
- Storage: `sol_storage! { #[entrypoint] pub struct C { uint256 total; mapping(address => uint256) balances; } }` — the layout is Solidity-slot-compatible; adding/reordering a field changes the slot of every later field.
- Environment: `msg::sender()`, `msg::value()`, `block::timestamp()`, and `contract::address()`.
- Cross-contract: `Call::new().call()`, `.static_call()`, `.delegate_call()`, and `caller`/`delegate` semantics (a `delegate_call` runs the callee's code against the caller's storage).
- Gas / ink: Stylus meters "ink" (WASM gas) in addition to EVM gas; `#[payable]`, and any call that burns ink in a loop.
- ABI: `#[public]` methods and `#[name]`/`#[selector]` overrides; the relation to Solidity selectors (`keccak256(signature)[0..4]`).

## Attack plan

1. Storage layout vs EVM slots: if a Stylus contract is deployed at (or upgrades) a Solidity contract's address, verify field-by-field that `sol_storage!` maps to the same slots. A reordered/add field makes an `owner` read a balance slot — silent corruption across the language boundary.
2. `sol_storage!` packing: Solidity packs small types into one slot; a Stylus struct that does not mirror the packing writes a neighbouring field. Dump slots with a Solidity `sload` tool and compare.
3. `msg::sender()` vs `caller`: for a proxy/`delegate_call` path, `sender` is the immediate caller; an authorization check on `sender` during a delegate call trusts the wrong identity (same trap as EVM `msg.sender` under `delegatecall`).
4. `delegate_call` storage clobber: Stylus permits `delegate_call` to arbitrary code with the caller's storage. An unvalidated delegate target can overwrite the contract's slots — full takeover.
5. `static_call` misuse: expecting `static_call` not to mutate, but the callee's WASM can re-enter through a path that writes; or using `call` where a read-only `static_call` was required (state change during a "view").
6. Reentrancy: Stylus gives no reentrancy guard. A method that calls out and then updates state is reentrant exactly as in Solidity; ink metering does not prevent it. A `delegate_call` back into the contract is especially dangerous.
7. Ink/gas griefing: a loop whose iteration count is caller-controlled burns ink until the WASM gas limit aborts. Even with EVM gas present, ink exhaustion reverts the call — a DoS on a shared entry point.
8. Rust panics: `unwrap()`, `expect()`, array indexing, integer overflow (panic in debug, wrap/revert in release) on user input aborts the whole call. Check what state is left and whether it bricks a shared path.
9. Selector compatibility: a Rust method exported with `#[name("transfer(address,uint256)")]` must hash to the same selector a Solidity caller uses. A wrong/overridden selector makes a call go to `fallback` or revert; two methods colliding is a mis-dispatch.
10. Value handling: `#[payable]` gates `msg::value()`; a non-payable method rejects ETH, and a payable method that ignores `msg::value()` strands it.

## Proof

- `cargo stylus check` (validates the WASM and ABI), `cargo test` for unit tests, `cargo stylus deploy` to a local Arb node.
- `cargo stylus export-abi` to inspect the generated Solidity ABI and confirm selectors.
- Use `cast sig "<signature>"` (Foundry) to compute the expected selector and compare to the exported ABI.
- For storage compatibility, `cast storage <addr> <slot>` against the Solidity layout and diff with the Stylus writes.
- For reentrancy/ink, an integration test via `ethers`/`cast` that re-enters; assert the double spend or the ink revert.

## Fix

- Keep `sol_storage!` layout identical to any Solidity contract sharing the address/slots; append-only on upgrades and verify slot-by-slot.
- Never trust `msg::sender()` as an identity under `delegate_call`; gate delegate targets to trusted, immutable code.
- Use `static_call` for read-only external calls; add a reentrancy guard (a storage flag) around any call that mutates shared state.
- Bound every loop; do not let caller input drive iteration count in a WASM entry point.
- Replace `unwrap()`/`expect()`/panic-prone arithmetic on user input with checked handling.
- Verify ABI selectors against `keccak256` of the signature and avoid overrides unless necessary.
- Require `#[payable]` only where value is consumed, and credit `msg::value()` explicitly.

## Severity and finding bar

- A Stylus/Solidity storage-slot mismatch that corrupts owner/balance is **Critical**.
- An unvalidated `delegate_call` target that clobbers storage is **Critical**.
- Reentrancy that double-spends is **Critical**; a missing guard on a non-value path is **Low**.
- Ink-exhaustion DoS is **Medium** to **High**; a Rust panic on a shared path is **Medium**.
- A selector mismatch is **Medium** unless it mis-dispatches to a privileged handler, then **High**.

## See also

- `ecosystems/evm` — Stylus shares the EVM ABI and storage model.
- `vulnerabilities/reentrancy`, `vulnerabilities/upgradeability-proxy`, `vulnerabilities/dos-griefing` — the general classes.
- `tooling/foundry` — for `cast`, `forge inspect`, and fork PoCs that straddle Solidity and Stylus.
