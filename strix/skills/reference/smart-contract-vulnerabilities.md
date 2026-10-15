---
name: smart-contract-vulnerabilities
description: kadenzipfel smart-contract-vulnerabilities taxonomy as a checklist with a one-line prevention for each bug class
---

# Smart-Contract Vulnerabilities Taxonomy

A checklist distilled from the kadenzipfel *smart-contract-vulnerabilities* catalog (its own grouping is Access Control, Math, Control Flow, Data Handling, Unsafe Logic, and Code Quality). Each item states the bug and a one-line prevention. Use it as a sweep list after the focused lenses, and cross-reference the sibling `vulnerabilities/*` skill for each class.

## Access control

- [ ] **`tx.origin` authorization** — never use `tx.origin` for auth; use `msg.sender`. Prevent: authorize on `msg.sender` plus an explicit role (`vulnerabilities/access-control`).
- [ ] **Insufficient access control** — an external function that changes critical state or moves value with no/weak guard. Prevent: enumerate entry points and add guards.
- [ ] **`delegatecall` to untrusted callee** — delegatecall into a caller-supplied address. Prevent: allowlist targets; never delegatecall user input.
- [ ] **Signature malleability** — accepting `(v, r, s)` with mutable `s` or high `v`. Prevent: enforce low-`s` and `v ∈ {27,28}`; use EIP-712 (`vulnerabilities/signature-replay`).
- [ ] **Signature replay** — a signature reuseable across calls/chains/contracts. Prevent: nonce + `chainid` + `address(this)` in the digest.

## Math

- [ ] **Integer overflow / underflow** — wrapping arithmetic (pre-0.8 or `unchecked`). Prevent: checked math (Solidity ≥0.8, `SafeMath`, Rust `checked_*`).
- [ ] **Off-by-one** — boundary errors in loops, bounds, and `<`/`<=`. Prevent: test the exact boundary values.
- [ ] **Lack of precision** — division before multiplication, truncation, dust. Prevent: multiply before divide; define rounding direction (`vulnerabilities/precision-rounding`).

## Control flow

- [ ] **Reentrancy** — external call before a state update; single-function, cross-function, or read-only. Prevent: checks-effects-interactions + reentrancy guard (`vulnerabilities/reentrancy`).
- [ ] **DoS with block gas limit** — an unbounded loop over a growing set. Prevent: bound iteration; pull over push.
- [ ] **DoS with unexpected revert** — one recipient's revert blocks all (e.g. `transfer` to a reverting address). Prevent: isolate failures; don't require every transfer to succeed.
- [ ] **`msg.value` in a loop** — `msg.value` reused across loop iterations. Prevent: account per-iteration; don't loop with a single value.
- [ ] **Transaction-ordering dependence** — outcome depends on tx order. Prevent: commit-reveal or slippage bounds (`vulnerabilities/mev-frontrunning`).
- [ ] **Insufficient gas griefing** — a relayer's gas can be starved by a callee. Prevent: forward enough gas or use a pull model.

## Denial of service

- [ ] **Unbounded external call in a critical path** — one bad token/pair bricks withdraw/liquidate. Prevent: try/catch with a fallback, or a pull design (`vulnerabilities/dos-griefing`).
- [ ] **Storage/gas growth** — arrays or mappings that only grow. Prevent: pruning or amortized cleanup.
- [ ] **Blocklist/pausable token** — an integrated token blocks the protocol address. Prevent: handle token-level pause/block (`reference/weird-erc20`).

## External calls / data handling

- [ ] **Unchecked return value** — ignoring `transfer`/`send`/low-level `call` result. Prevent: check or use `SafeERC20` (`vulnerabilities/unchecked-returns`).
- [ ] **Unsafe low-level call** — `call`/`callcode` with ignored failure or arbitrary target. Prevent: check success; restrict target.
- [ ] **Write to arbitrary storage location** — array/length manipulation or unchecked assembly `sstore`. Prevent: no user-controlled storage indices.
- [ ] **Unbounded return data** — `returndatacopy` of attacker-sized data. Prevent: bound the copy size.
- [ ] **Uninitialized storage pointer** — writing through an unset storage reference. Prevent: initialize all storage references.
- [ ] **Unexpected `ecrecover` null address** — bad signature returns `address(0)`. Prevent: `require(signer != address(0))`.
- [ ] **`abi.encodePacked` hash collision** — variable-length args collide. Prevent: `abi.encode` for hashing.

## Randomness

- [ ] **Weak randomness from chain attributes** — `block.timestamp`, `blockhash`, `block.difficulty`/`prevrandao`, `block.coinbase`. Prevent: commit-reveal or a VRF.
- [ ] **Timestamp dependence** — logic that assumes exact timing or uses time as entropy. Prevent: tolerate miner drift; never treat time as random.

## Upgradeability

- [ ] **Storage collision on upgrade** — inserting/reordering variables in a proxy. Prevent: append-only layout; storage-gap patterns (`vulnerabilities/upgradeability-proxy`).
- [ ] **Unprotected `initialize` / `upgradeTo`** — front-runnable or unguarded. Prevent: initializer gating and an upgrade guard.
- [ ] **`selfdestruct` / `delegatecall` in the implementation** — breaks proxy state. Prevent: forbid in proxied logic.

## Token quirks

- [ ] **Non-standard ERC-20** — no return value, `false` on success, fee-on-transfer, rebasing, blocklist, decimals ≠ 18. Prevent: measure balances, use `SafeERC20`, allowlist tokens (`reference/weird-erc20`).

## Code quality

- [ ] **Floating pragma / outdated compiler / deprecated functions** — pin and update (use a recent, checked compiler).
- [ ] **Incorrect constructor name / default visibility / shadowing** — verify intent; make visibility explicit.
- [ ] **Incorrect inheritance order** — C3 linearization surprises. Prevent: explicit, reviewed linearization.
- [ ] **Assert vs require misuse** — `assert` for input validation burns gas; use `require`.

## Sources

- kadenzipfel smart-contract-vulnerabilities: https://github.com/kadenzipfel/smart-contract-vulnerabilities
- Companion skills: `vulnerabilities/*`, `reference/weird-erc20`, `reference/scsvs-checklist`.
