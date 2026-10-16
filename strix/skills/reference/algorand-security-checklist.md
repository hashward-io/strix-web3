---
name: algorand-security-checklist
description: Algorand (AVM) security checklist — atomic transaction groups, sender and rekey, inner transactions, boxes, assets and logic sigs
---

# Algorand (AVM) Security Checklist

A checklist for reviewing Algorand applications (PyTeal/Beaker, TEAL, Algorand Python) and logic signatures. The AVM executes whole **atomic groups**: a validator sees its own transaction and can read the others. The distinctive bugs are **unvalidated group composition**, **rekeying**, and **inner transactions**.

## Group & transaction validation

- [ ] **Unvalidated group composition** — the app does not check `Global.group_size`, the group id, its own position (`Txn.group_index`), and the type/fields of the other transactions it relies on (`vulnerabilities/algorand-group-transactions`).
- [ ] **Duplicate transaction / double-count** — the same payment or asset transfer counted for two actions in a group.
- [ ] **Untrusted `gtxn` fields** — reading another transaction's amount/receiver/sender without checking who controls it.
- [ ] **`App.id == 0` at creation** — code that treats the app id as known during the creation call.

## Sender, rekey & accounts

- [ ] **Unchecked `Txn.sender`** — an action gated on the sender without verifying the expected address, or trusting `Txn.accounts[i]` as the sender (`vulnerabilities/algorand-account-and-rekey`).
- [ ] **Missing rekey protection** — an attacker sets `RekeyTo` to their own account and takes over the account (the classic AVM takeover). Prevent: reject `RekeyTo` unless explicitly intended, and wildcard `RekeyTo == ZeroAddress` checks. Rekeying a contract account to an attacker is critical.
- [ ] **Close-remainder** — `CloseRemainderTo` draining the account balance.
- [ ] **Asset opt-in/clawback/freeze** — assuming an asset cannot be clawed back or frozen, or a transfer that does not check `AssetSender`/`AssetReceiver`.

## Inner transactions

- [ ] **Unauthorized inner txn** — an inner `itxn` (payment/asset/appl) sent without verifying the caller and amount (`vulnerabilities/algorand-inner-and-storage`).
- [ ] **`Global.calldepth` not bounded** — a reentrant path via inner application calls.
- [ ] **Fee pooling** — a group with pooled fees where an attacker funds another transaction.

## Boxes, state & storage

- [ ] **Box reference omitted** — an app touching a box without declaring it in the box references.
- [ ] **Global vs local state mutation** — an action that writes global state where local was intended, or vice versa.

## Logic signatures

- [ ] **Unvalidated logic-sig args** — a delegate signature (`arg`) not checked, or a signature that authorizes more than intended.

## Validation

- [ ] Reproduce with AlgoKit (`algokit-utils` + pytest, or a localnet you operate) by crafting the malicious atomic group (including a `RekeyTo`/`CloseRemainderTo` and a duplicate-txn group), asserting the unauthorized state change.
- [ ] `algokit compile` and diff the approved program/clear program against source.
