---
name: cardano
description: Cardano eUTxO playbook - Aiken and Plutus (V1/V2/V3) validators; datum/redeemer/script context, double satisfaction, continuation outputs, native tokens and minting policies, aiken CLI
---

# Cardano Ecosystem

Cardano is an **extended UTxO (eUTxO)** ledger: every output carries a value and optionally a datum, and a validator is a pure function of (datum, redeemer, script context). Security is about what the transaction *also* does — which outputs exist, what value is minted, and whether the continuing state was actually checked.

## When to use

- An Aiken project (`aiken.toml`, `validators/*.ak`, `lib/*.ak`) or a `plutus.json` blueprint.
- Plutus/`plutus-tx` sources, `*.plutus` scripts, or `cardano-cli`/`cardano-testnet` scripts.
- TypeScript transaction builders (Lucid, Mesh) or an obvious `datum`/`redeemer`/script-context model.
- You need the eUTxO bug-class map before narrowing to `vulnerabilities/cardano-*`.

## Detecting the target

- Aiken: `aiken.toml`, `.ak` files under `validators/` and `lib/`, `plutus.json` after `aiken build`.
- Plutus: `*.hs` importing `PlutusLedgerApi`, `*.plutus`, or a `plutus-tx` project.
- Off-chain: `lucid-cardano` / `lucid-evolution` / `@meshsdk/core` scripts, or `cardano-cli` shell scripts.

## Contract models

- **Aiken `validator`:** one script with one or more handlers (`spend`, `mint`, `withdraw`, `certify`, `publish`, `vote`). A handler returns `Bool` or, better, a `Transaction` continuation the ledger then enforces.
- **Plutus:** validators as `CompiledCode`/`Script`; V1/V2/V3 differ in the shape of `ScriptContext`.
- **eUTxO state:** a script's "state" is the datum on its UTxOs, so a state transition means spending the old UTxO and creating a new one.

## The eUTxO security model

- A transaction consumes **inputs** and creates **outputs**; nothing ties a specific input to a specific output unless the validator enforces it.
- A spending validator sees `datum`, `redeemer`, and the **script context**: all inputs, all outputs, `mint`, `fee`, `validity_range`, and `extra_signatories` (the transaction's required signers).
- **Value** is a nested map `PolicyId -> AssetName -> quantity`; ADA is policy `#""` with asset name `#""`.
- Several script inputs can each require the *same* output property in one transaction — the origin of **double satisfaction**.

## Where the bugs live

- **Double satisfaction & continuation** — an output that satisfies two validators; a validator that never checks the continuing UTxO (address, value, datum) or trusts output ordering. See `vulnerabilities/cardano-eutxo-double-satisfaction`.
- **Datum / redeemer / context** — trusting the datum or an attacker-chosen redeemer, misreading the script context, validity range, or required signers, or reusing a script across purposes. See `vulnerabilities/cardano-datum-redeemer-context`.
- **Value & minting** — counterfeit tokens, non-normalized `Value`, non-one-shot minting policies, missing lovelace/min-UTxO checks. See `vulnerabilities/cardano-value-and-minting`.

## Toolchain & build

- Aiken: `aiken build` (emits `plutus.json`), `aiken check`, `aiken test`, `aiken fmt`, `aiken docs`.
- Local cluster: `cardano-testnet`; transaction building with `cardano-cli` or Lucid/Mesh.
- See `tooling/aiken` for the full command reference.

## Proof standard

`aiken test` fixtures build a `Transaction` (the script context) directly and assert the validator *accepts* an attacker's transaction — the cheapest, most reliable PoC. For end-to-end evidence, run `cardano-testnet` and submit a Lucid/`cardano-cli` transaction that succeeds while breaking the protocol rule. A code read is a **lead**; the confirmed finding names the exact missing output/datum/value check.

## Testing

- `aiken test` with fixture builders from the standard library (`aiken/transaction`, `aiken/transaction/value`).
- Model both the honest and the malicious transaction; the validator's verdict must differ only because a check is missing.
- For value bugs, assert `value.quantity_of` on the produced outputs.
- Run `aiken check` for type/pattern errors and `aiken fmt` before keeping the test as evidence.

## Fix patterns

Always validate the continuing output (address, value, datum) against the input being spent; bind outputs to specific inputs by carrying the `OutputReference` in the datum; treat datum, redeemer, and context as attacker-controlled; use `value.quantity_of`/`value.flatten` for exact token checks; make minting policies one-shot; enforce min-ADA and required signers. See `vulnerabilities/cardano-eutxo-double-satisfaction`, `vulnerabilities/cardano-datum-redeemer-context`, `vulnerabilities/cardano-value-and-minting`, and `hacking_agents/invariant`.
