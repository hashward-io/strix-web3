---
name: aiken
description: Aiken toolchain for Cardano - aiken new/build/check/test/fmt/docs, plutus.json blueprint, aiken-lang/stdlib fixtures, cardano-cli/cardano-testnet and Lucid/Mesh for end-to-end proofs
---

# Aiken (Cardano)

Aiken compiles to Plutus and ships a first-class test runner, which makes it the fastest way to prove a Cardano validator bug: build a `Transaction`, run the validator, assert the verdict.

## Install / build

- Install: `curl -sSfL https://install.aiken-lang.org | bash`, then `aiken --version`. `aikup` manages versions.
- New project: `aiken new <org>/<project>`, then `aiken build`.
- `aiken build` compiles validators to UPLC and writes `plutus.json` (the CIP-57 blueprint) plus the validator hashes/addresses.

## Core commands

```
aiken new <org>/<name>          # scaffold validators/, lib/, aiken.toml
aiken build                     # compile; writes plutus.json
aiken check                     # type-check and report warnings
aiken test                      # run tests/ (the proof harness)
aiken fmt                       # format sources
aiken docs                      # generate documentation from the blueprint
```

## The blueprint and addresses

- `plutus.json` (CIP-57) is the compiled blueprint; tools load a validator by its hash.
- A script's on-chain address is derived from the validator hash — `cardano-cli address build`, or Lucid's `validatorToAddress`.
- Rebuild after every edit so the blueprint hash and address stay current.

## Writing a proof with `aiken test`

- Import `aiken/transaction`, `aiken/transaction/value`, and `aiken/transaction/credential`.
- Build a `Transaction` value that stands in for the script context: inputs, outputs, `mint`, `validity_range`.
- Call the validator handler with a malicious datum/redeemer and that context, then assert the result.
- The handler signature depends on the Aiken version: older handlers take a single `ScriptContext`, newer ones take `datum, redeemer, own_ref, self`.

```aiken
use aiken/transaction/value

// Build the attacker's context, then run the handler and assert it accepts.
test malicious_context_is_accepted() {
  let ctx = build_attacker_context()   // your fixture
  my_validator.spend(Some(attacker_datum), attacker_redeemer, ctx)
    |> is_ok
}
```

## End-to-end (optional)

- `cardano-testnet` starts a local cluster; build and submit with `cardano-cli` or Lucid/Mesh.
- Load the script from `plutus.json`; derive its address with Lucid (`validatorToAddress`) or `cardano-cli`.

## Audit workflow

1. `aiken check`, then read `plutus.json` to enumerate validators and their handlers.
2. For each handler, list what it reads from the transaction and what it never checks.
3. Write a test that submits the attacker transaction; a returned `Ok` is the finding.
4. `aiken fmt` and keep the test under `tests/` as the runnable PoC.

## Pitfalls

- A test that builds an impossible context proves nothing; mirror real ledger rules (fees, min-ADA).
- `aiken check` warnings about unchecked `expect`/unused values often mark a missed validation.
- Blueprint drift: a stale `plutus.json` gives the wrong hash/address and invalidates the PoC.
- Tests assert *behavior*, not intent — re-derive assertions from the protocol's rules, not from the code.
