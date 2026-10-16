---
name: bitcoin-security-checklist
description: Bitcoin Script security checklist — sighash coverage, covenant and timelock logic, script-path breadth, amount and fee handling
---

# Bitcoin Script Security Checklist

A checklist for reviewing Bitcoin Script, Miniscript policies, taproot trees, and covenant-style contracts. The distinctive bugs are **sighash coverage**, **covenant/timelock logic**, and **spending-path breadth** — Bitcoin has no general computation, so a mistake is usually a script that authorizes more than intended.

## Sighash & signature coverage

- [ ] **Narrow sighash** — `SIGHASH_NONE`/`SIGHASH_SINGLE`/`ANYONECANPAY` lets an attacker change outputs, amounts, or the recipient after signing (`vulnerabilities/bitcoin-script-covenants`).
- [ ] **Amount not committed** — legacy (pre-segwit) signatures did not commit the input amount; a signing device can be tricked about value.
- [ ] **`OP_CHECKMULTISIG` off-by-one** — the dummy element / `n`/`m` ordering bug that changes the threshold.
- [ ] **Pubkey not pinned** — `OP_CHECKSIG` against a key the attacker supplies, or a `OP_CHECKSIGADD` threshold that is lower than intended.

## Covenants, timelocks & script paths

- [ ] **Anyone-can-spend branch** — a script path (e.g. an `OP_ELSE`/`OP_0` branch, or a taproot leaf) that always evaluates true.
- [ ] **Timelock semantics** — `OP_CHECKLOCKTIMEVERIFY`/`OP_CHECKSEQUENCEVERIFY`: wrong units (height vs time), a locktime the transaction does not match, or a relative lock not bound to the right input.
- [ ] **Covenant not enforced** — a "covenant" that constrains outputs only on one branch, or checks the output value/script incorrectly (output ordering, dust, fee).
- [ ] **Taproot key-path bypass** — an internal key that can spend the output directly, bypassing the script-path policy.
- [ ] **Malleable witness** — a witness/script that can be replaced without invalidating the spend, breaking downstream assumptions.

## Amount, fee & policy

- [ ] **Fee theft / RBF** — a path that lets a counterparty replace or over-fee the transaction.
- [ ] **Change and dust** — change sent to an uncontrolled script, or an output below the dust threshold that is uneconomic to spend.
- [ ] **Miniscript policy mismatch** — the compiled `miniscript` does not match the stated policy (missing `and_v`, wrong `thresh`).

## Validation

- [ ] Reproduce on `bitcoind` regtest: broadcast the crafted spend (narrow sighash, wrong threshold, alternate script path) and confirm it is accepted when it should be rejected.
- [ ] Decode and re-derive the script with `bitcoin-cli decodescript` / `rust-miniscript` and compare to the intended policy.
