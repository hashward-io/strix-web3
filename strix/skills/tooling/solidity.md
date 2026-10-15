---
name: solidity
description: Solidity language and security idioms — versions, data locations, visibility, and the language footguns that cause bugs
---

# Solidity Language and Footguns

Know the language rules; most "weird" bugs are the language doing exactly what it says.

## Version and semantics

- **`^0.8.0`:** checked arithmetic by default (overflow reverts); `unchecked { }` re-enables wrapping. Below 0.8, arithmetic wraps silently — treat every `+`/`-`/`*` as suspect.
- **Custom errors vs `require` strings:** behaviorally equivalent; both revert.
- **`0.8.x` `abi.encodeCall`** and named-argument struct construction reduce positional mistakes.

## Data location and memory

- `calldata` (immutable, cheap) vs `memory` vs `storage` (reference to state). Passing a `memory` array and mutating it does **not** change storage; passing `storage` and mutating does.
- `storage` pointers can alias: two pointers to the same slot written through different paths.
- Copy semantics: `storage → memory` copies once; assignments between `storage` structs copy field by field (and can be gas-heavy or partial).

## Visibility and inheritance

- `external` vs `public` (public is callable internally too); `internal`/`private` (private is still visible in the compiled bytecode and callable via `delegatecall` in some layouts — never rely on `private` for secrecy).
- **`override`/`virtual`:** a child override can silently change a parent's behavior; `super` chains order matters (linearization: C3).
- **Diamond/multiple inheritance:** storage slot order follows linearization; a mismatch between inherited layouts is a collision (see `vulnerabilities/upgradeability-proxy`).
- **Constructors vs initializers:** constructor state does not exist behind a proxy.

## Types

- `address` vs `address payable` (a `.transfer` needs payable); `uint256` vs `uint128` casts truncate.
- Fixed-size vs dynamic arrays/bytes; `.length` on a storage array can be pushed to; `bytes32` vs `string` comparison.
- `enum` casts from out-of-range integers revert; `bool` from non-0/1 is not normalized.
- `mapping` iteration is not possible directly — a bug is often an attempt to iterate via an auxiliary array that gets out of sync.

## External calls

- `.call{value:}("")` vs `.transfer` (2300 gas) vs `.send` (returns bool). Use `.call` and check success; avoid `.transfer` for variable-gas recipients.
- `delegatecall` runs callee code with caller storage/`msg.sender`/`address(this)`.
- `staticcall` forbids state change; a `view` that calls a non-view via `staticcall` reverts.
- Return data of a `.call` to an EOA is empty and `success == true`.

## Common footguns checklist

- `tx.origin` for auth; `block.timestamp` for randomness; `block.number` for time.
- `abi.encodePacked` collisions (e.g. `encodePacked(a, b)` where `a`,`b` are dynamic strings can collide with a different split) — use `abi.encode`.
- Uninitialized storage pointers (a local `storage` var with no assignment points to slot 0) — a pre-0.5 bug, but still seen in old code.
- `keccak256` of a `string` vs `bytes`; no length prefix in a hash of concatenated dynamic data.
- `require` with side effects inside the boolean expression.
- `selfdestruct`/`delegatecall` to attacker-controlled targets.

## How to use this skill

When a finding seems "impossible", re-read the relevant language rule above — the code is usually doing what the language actually specifies, and the bug is the author's mental model.
