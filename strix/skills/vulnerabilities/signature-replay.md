---
name: signature-replay
description: Signature and permit issues — replay, malleability, ecrecover misuse, missing nonce/chainId/domain, and path confusion
---

# Signature Replay and Validation

Off-chain authorization is only as good as the code that verifies it. Every missing component becomes a replay.

## Where to look

- **Replay across chains** — a signature without `chainId` (or with a hard-coded one) can be replayed on a fork or another chain (post-merge, `block.chainid` is the check; a fork shares it, so also consider a fork-specific `domainSeparator`).
- **Replay within a chain** — no per-signer nonce, or a nonce that is not incremented on use, or a nonce that is not part of the signature. The same signed message can be submitted twice.
- **Replay across contracts** — no `verifyingContract` in the EIP-712 domain, so a signature valid on contract A is valid on contract B with the same shape.
- **`ecrecover` misuse** — accepts `v` other than 27/28; does not reject `s > secp256k1n/2` (malleable: two valid signatures for one message); returns `address(0)` for invalid input and the code treats `address(0)` as a valid signer or an "allow all"; does not check the recovered address is non-zero.
- **Typed-data confusion** — the hash binds fewer fields than the action uses, or binds them in the wrong order, or omits a field (e.g. `deadline`, `amount`, `to`) that a later step relies on.
- **Permit issues** — EIP-2612 `permit` with no deadline check, a `spender` not bound, or a front-run that turns a `permit`+`transferFrom` into a griefing vector; DAI-style permit with a wrong `nonces` mapping.
- **Signature as access control** — a "the operator signed this" check where any signature over a reusable payload grants standing authority.
- **`isValidSignature` (ERC-1271)** — contract-wallet validation that returns magic on arbitrary data, or does not restrict `_hash`.
- **Cross-function reuse** — the same signature struct used by two functions with different semantics.

## Attack plan

1. Enumerate every signed payload: its fields, its domain, its nonce, its deadline.
2. For each field the payload omits but the action uses, craft the divergent second use.
3. Check `ecrecover` inputs for malleability and zero-address acceptance.
4. Try to submit the same signature twice; then on a second contract; then with a mutated but valid `s`.

## Proof

Show the replay: capture/hold a valid signature and submit it a second time (or on another contract/chain) with the same effect, or show the malleability by producing two valid signatures for one `(v, r, s)` message. A Foundry PoC that replays is ideal.

## Fix

Use EIP-712 with a full domain (`name`, `version`, `chainId`, `verifyingContract`); include and consume a per-signer nonce; include a `deadline`; enforce `v ∈ {27,28}`, `s ≤ secp256k1n/2`, and `recovered != address(0)` (or use OpenZeppelin `ECDSA`/`EIP712`, which do).
