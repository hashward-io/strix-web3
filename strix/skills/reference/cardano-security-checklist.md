---
name: cardano-security-checklist
description: Cardano security checklist — eUTxO double satisfaction, datum/redeemer/context, value and minting, signature and validity checks
---

# Cardano Security Checklist

A checklist for reviewing Cardano validators (Aiken, Plutus/PlutusTx, Marlowe) and minting policies. In the eUTxO model a validator runs **only for the input being spent** and returns a `ScriptContext` built from the whole transaction. The distinctive bugs are **double satisfaction**, **context misreads**, and **forgery**.

## eUTxO structure

- [ ] **Double satisfaction** — one output satisfies the requirements of two different validators (a single payment counted for two swaps). Prevent: bind each expected output uniquely (address + value + datum), or use a singleton/thread token (`vulnerabilities/cardano-eutxo-double-satisfaction`).
- [ ] **Missing continuation check** — a stateful validator that does not verify the continuing output's address, value, and datum (so state can vanish or be forged).
- [ ] **Output ordering assumed** — code that trusts outputs by index when an attacker can reorder.
- [ ] **Own script hash not checked** — the continuing output's address is not verified to carry this validator's hash, allowing wrapping in a different script.

## Datum / redeemer / context

- [ ] **Trusting the datum** — a validator that reads the datum as truth without verifying it is the intended one (datums are attacker-supplied) (`vulnerabilities/cardano-datum-redeemer-context`).
- [ ] **Redeemer not constrained** — any redeemer is accepted, so the attacker picks the branch.
- [ ] **Purpose confusion** — a validator reused across `Spend`/`Mint`/`Withdraw`/`Publish` purposes without checking `ScriptContext.purpose`.
- [ ] **Signature check mismatch** — checking `tx.info.signatories` for a key but not that it is the *right* key (or checking a key that anyone can satisfy). Require the expected verification key hash.
- [ ] **Validity range ignored** — a time-locked action without checking `tx.validity_range` (or a range an attacker can choose).

## Value & minting

- [ ] **Native-token forgery** — a minting policy that mints an unbounded amount, or a non-one-shot NFT policy (no UTxO/nonce consumed) (`vulnerabilities/cardano-value-and-minting`).
- [ ] **Non-normalized `Value`** — assuming a single entry per asset; `Value` can list an asset twice, and a negative mint amount enables forgery.
- [ ] **Lovelace minimum / min-UTxO** — an output below the min-UTxO that makes funds unspendable.
- [ ] **Collateral** — a script that can only be validated with collateral assumptions that fail on-chain.

## Validation

- [ ] Reproduce with Aiken's `aiken check`/test framework or a Plutus/Aiken test harness by constructing the malicious transaction (double-satisfaction witness, forged datum, reordering), asserting the unauthorized state change.
- [ ] `aiken build` and verify the script hash committed to source matches the deployed address.
