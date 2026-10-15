---
name: account-abstraction
description: ERC-4337 and smart accounts — UserOperation validation vs execution, paymaster trust, session keys, EIP-7702 delegation, and bundler/MEV risks
---

# Account Abstraction / Smart Accounts

Account abstraction splits a transaction into a `UserOperation` that the account validates and an
execution the singleton EntryPoint performs later. The gap between "who validated this" and "who can
execute it" is where the bugs live.

## Domains

- **Validation vs execution phase.**
  - `validateUserOp` runs during validation; `execute`/`executeBatch` run during execution.
  - Anything read in validation (`block.timestamp`, storage, an external call) can differ by execution time.
  - `simulateValidation`/`simulateHandleOp` are advisory; do not assume they see final state.
- **Time ranges.** `validAfter`/`validUntil` and the packed `validationData` (`authorizer | validUntil | validAfter`) are trusted by the EntryPoint. A wrong mask or a `0` sentinel makes an operation valid forever or immediately.
- **Hash binding.** `userOpHash` must bind `chainId`, `EntryPoint`, `sender`, `nonce`, `callData`, `paymasterAndData`, and gas fees. Remove each field in the recomputation to find one the hash omits.
- **Signature validation.**
  - ERC-1271 accounts return the magic value; EOA accounts `ecrecover`.
  - Check `v ∈ {27,28}`, low-`s`, and a non-zero recovered address (`vulnerabilities/signature-replay`).
  - Passkey / P-256 paths (WebAuthn, RIP-7212) add curve and precompile edge cases.
- **Nonces.** Nonces are two-dimensional (`key | sequence`); `getNonce(sender, key)` is the read surface. A reused key, a sequence that is not incremented, or an attacker-chosen key defeats ordering.
- **Paymaster trust.**
  - `paymasterAndData` is parsed twice — once by the EntryPoint, once by the paymaster. A length/offset mismatch lets the two disagree.
  - `validatePaymasterUserOp` must verify the user's signed approval and a deposit/stake.
  - `postOp` runs after execution and can revert or re-enter; `context` is trusted across phases.
- **Token paymasters.** Gas is priced in a token through an oracle; a stale or manipulable price lets a user over- or under-pay (`vulnerabilities/oracle-manipulation`).
- **EntryPoint trust.** Only the canonical EntryPoint may call `validateUserOp` and the account's execution entry. A missing `msg.sender == entryPoint` check lets anyone drive the account.
- **Account implementation.** `execute(target, value, data)` with attacker-controlled args is `delegatecall`-adjacent. Upgradeable accounts (proxy + initializer) can be re-initialized; owner and module registries can be reassigned.
- **Modules.** ERC-7579 / ERC-6900 modules widen the privilege surface — validator, executor, hook, and fallback modules each call back into the account.
- **Session keys.** Scoped keys with spending limits, allowed targets/selectors, and expiry. Check limits across a batch, expiry validated in the validation phase, and real revocation.
- **EIP-7702 delegation.** An EOA installs code via an authorization tuple (`chain_id`, `address`, `nonce`, `yParity`, `r`, `s`) and the designator `0xef0100 || implementation`. The nonce must be consumed and the tuple bound to chain and implementation.
- **Bundler / MEV.** The bundler chooses inclusion and ordering; fee payment to `msg.sender` in the EntryPoint can squeeze a depositor. Staked validators can be griefed or throttled under the reputation system.
- **Non-EVM analogue.** On Solana, "smart accounts" are PDAs plus delegated authority and durable nonces. Check versioned transactions, address-lookup-table substitution, `secp256k1`/`ed25519` instruction introspection, and PDA-as-authority seeds (`ecosystems/solana`).

## Where to look

- `EntryPoint.handleOps`, `handleAggregatedOps`, `simulateHandleOp`, `getUserOpHash`, `getNonce`, `depositTo`, `addStake`.
- Per-sender `deposits` and `stakes`; `requiredPrefund`, unused-gas refund, and who receives the bundle penalty.
- Account `validateUserOp`, `execute`, `executeBatch`, `_validateSignature`, `entryPoint()`, `getNonce`, `initialize`.
- Module install/uninstall and the allowed-module registry.
- Paymaster `validatePaymasterUserOp`, `postOp`, `getHash`, `deposit`, token/oracle pricing.
- Aggregator `validateSignatures`, `validateUserOpSignature`, `aggregateSignatures` — check the aggregator address carried in `validationData`.
- EIP-7702 authorization tuples and the `0xef0100` designator appearing in deployed code.
- Events: `UserOperationEvent`, `AccountDeployed`, `UserOperationRevertReason` for replay evidence.

## Attack plan

1. Recompute `userOpHash` from the struct and compare to the implementation's fields; drop each field to find one the hash omits.
2. Trace every external caller of `validateUserOp`/`execute` and test the missing EntryPoint check.
3. Replay: submit the same `UserOp` twice (same nonce key), then a second time on a fork or another chain.
4. Attack the paymaster: spoof `paymasterAndData`, extract `postOp` context, or drain a token paymaster via a stale oracle.
5. For EIP-7702, replay an authorization tuple or point it at a proxy with a live initializer.
6. Assume the bundler is adversarial: test fee extraction and validator griefing (`protocols/governance` for the stake/throttle boundary).

## Proof

A Foundry PoC against a forked EntryPoint (or the repo's mock): craft a signed `UserOperation` and show a
second execution, an unauthorized `execute`, a paymaster drain, or fee overpayment. Quantify value. If you
can only show a missing check without a reachable trace, file it as a **lead**, not a finding
(`analysis/finding-contract`).

## Fix / Mitigations

Gate the account's validation and execution on `msg.sender == entryPoint`; hash every security-relevant
field into `userOpHash`; consume nonces per key and validate time ranges in the validation phase; have the
paymaster verify a signed user approval and re-derive `paymasterAndData` offsets safely; price token
paymasters with a manipulation-resistant oracle; make initializers idempotent and modules revocable; consume
7702 authorization nonces and never delegate to an uninitialized proxy; document bundler/EntryPoint trust.
