---
name: sharp-edges
description: Audit the protocol's own API for footguns — dangerous parameter combinations, silent truncation, surprising units, overloaded semantics
---

# Sharp Edges

A sharp edge is a footgun in the protocol's own interface: an API that is correct on the happy path but that a caller — the protocol itself, a keeper, an integrator, or an attacker — can misuse because the interface makes misuse easy and silent. Not every sharp edge is a vulnerability, but every sharp edge is a place to hunt. Audit the API as if you were the worst-behaved caller.

## Categories of sharp edge

**Dangerous parameter combinations.** Two parameters that are individually valid but catastrophic together. Examples: `slippage == 0` plus a public mempool; `deadline == 0` meaning "never expires"; `recipient == address(0)`; `amount == type(uint256).max` interpreted as "all"; `minOut > maxOut`; a `deadline` in the past accepted silently. Enumerate the parameters, then ask which pair or triple breaks a guard.

**Silent truncation / casting.** Solidity `uint256 → uint128 → uint64` downcasts that wrap or truncate without a check (`SafeCast` missing); Rust `as u64` on a `u128`; `felt252` forced into `u128`; a Move `u64 → u8`; a CosmWasm `Uint256 → Uint128`. A value that survives the API but not the cast is a bug. Also: `abi.encodePacked` of variable-length args causing hash collisions.

**Surprising units.** Basis points vs percent vs per-1e18 vs per-1e6; seconds vs blocks vs slots; `decimals` of the input token vs a hardcoded `1e18`; yoctoNEAR vs NEAR; lamports vs SOL; a `rate` per-second vs per-year. A unit mismatch usually multiplies or divides value by 10x–1e12x. Grep every literal and every `10**n`.

**Overloaded semantics.** One value meaning several things depending on a flag: `amount == 0` = "all" vs "nothing"; `token == address(0)` = native vs invalid; `mode` enum with an implicit default; a `bool isBuy` that flips rounding. The caller must know the branch the code takes; the attacker will pick the favorable one.

**Ordering and precedence.** Operations in an order the caller cannot control deterministically; a `swap` that trusts an `amountIn` computed before a fee; a fee applied after a cap; rounding applied before vs after a multiplication. Compare the order in the contract to the order the spec implies.

**Return-value and failure semantics.** A function that returns `false` instead of reverting; a low-level `call` whose success bit is ignored; a `try/catch` that swallows the error and continues with stale state; a `transferFrom` that returns `true` but moves less (fee-on-transfer). See `vulnerabilities/unchecked-returns` and `vulnerabilities/token-integration`.

**Callbacks / reentries the API invites.** A hook parameter (`to`, `data`, `callback`) the caller supplies; an ERC-777/ERC-1155 recipient; a `permit` with a non-standard implementation. The API promises the callback is inert; the attacker makes it re-enter.

**Unbounded / gas-bombing inputs.** An array length the API accepts but the loop cannot finish; a string/cell recursion depth; return data copied with `returndatacopy` unbounded; a Merkle branch length. The API is safe per-item and fatal in aggregate.

## Cross-ecosystem notes

- EVM: downcasts, `abi.encodePacked`, `delegatecall` target params, `approve`-race semantics, `uint96` token caps.
- Solana: `u64` lamport math, remaining-accounts trust, `has_one` vs manual checks, duplicate mutable accounts.
- Move: abilities as API contracts (`copy`/`drop`/`store`/`key`), `public(friend)` widening, generic `type` substitution.
- Cairo: `felt252` and `u256`/`i128` casts, `#[external(v0)]` overloads, `selector!` collisions.
- CosmWasm: `info.funds` vs a claimed amount, `Uint128` vs `Decimal`, `submessages` reply IDs.
- ZK: public-input ordering/units, an under-constrained hint that the API "guarantees".

## Attack plan

1. For each public surface, list parameters and their accepted ranges.
2. For each pair/triple of parameters, ask which combination defeats a guard or a rounding assumption.
3. Grep for downcasts, literal `10**n`, `0` sentinels, `type(..).max`, and `block.timestamp`/`slot` comparisons.
4. For each, construct the worst-behaved caller and trace the effect.

## Worked micro-example

`swap(amountIn, minOut, deadline, to)`:
- `amountIn == type(uint256).max` is overloaded to mean "all" → a caller who passes it by accident spends everything.
- `deadline == 0` never expires → a stale transaction executes at a bad price.
- `minOut == 0` in a public mempool → sandwich.
- `to == address(0)` accepted → value sent to the zero address.

Each parameter is fine alone; the API's own sentinels make the dangerous combinations invisible to a careless caller. Report the combination, not each parameter.

## Proof

A call sequence with concrete malicious parameter values that produces an unintended effect (value moved, invariant broken, DoS). Name the parameter combination and the branch it takes.

## Fix

Reject dangerous combinations explicitly; use checked casts (`SafeCast`, `u128::try_from`); document and enforce units in names and comments; eliminate overloaded sentinels; revert on failure instead of returning `false`; bound loop/recursion inputs.

## How to apply

1. Enumerate every public/external/entry surface in the codebase.
2. For each, list parameters, units, sentinels, and accepted ranges.
3. Ask "what is the worst caller I can be?" and try the combinations, casts, and ordering that break a guard.
4. Keep every sharp edge as a LEAD until you have a concrete call that reaches an impact; then promote with a PoC.
5. Cross-check each edge against `hacking_agents/boundary` and `hacking_agents/numerical-gap`.
