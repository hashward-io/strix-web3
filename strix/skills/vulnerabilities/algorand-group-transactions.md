---
name: algorand-group-transactions
description: Algorand atomic group composition bugs - unvalidated Gtxn fields, group-size/index confusion, fee pooling, group replay, unvalidated amount, receiver, or asset
---

# Group Transaction Composition (Algorand)

An Algorand **atomic group** is up to 16 transactions that succeed or fail together. A contract that reads a sibling with `Gtxn[i]` and trusts what it finds there is trusting attacker-supplied data: nothing in the runtime checks that the adjacent transaction is the type, sender, amount, or asset the contract assumes.

## Where to look

- **`Gtxn[i]` / `gtxn` / `gtxns` / `gtxnsa`** — reads of sibling transactions. Each read must be validated on `type_enum`, `sender`, `receiver`, `amount`, `xfer_asset`, `asset_amount`, `asset_receiver`, and `application_id` before it is trusted.
- **`Txn.group_index`** — the contract's own position. A hard-coded index (`Gtxn[0]`, `Gtxn[1]`) is wrong the moment the contract is not at that slot; use the index relative to `Txn.group_index`.
- **`Global.group_size`** — a missing check lets a lone transaction satisfy logic written for a 2+ transaction group.
- **`gtxns` / `gtxnsa`** — the sibling index comes from the stack; if it is derived from `Txn.group_index` arithmetic, an off-by-one or unchecked value reads the wrong transaction.
- **`Txn.fee` — fee pooling.** The group's fees sum and any member may pay, so a logged check like `Txn.fee >= X` is bypassable when a sibling pays.
- **Payment/asset fields** — `Txn.amount`, `Txn.receiver`, `Txn.close_remainder_to`, `Txn.xfer_asset`, `Txn.asset_amount`, `Txn.asset_sender`, `Txn.asset_close_to`.
- **Inner groups** — `itxn_next` builds a multi-inner group; the same "trust the sibling" mistake applies to inner transactions.
- **`Txn.tx_id` / `Txn.group_id`** — a transaction id identifies one txn and the group id binds the whole group; without them any txn with the expected fields can be swapped in.
- **`Txn.first_valid` / `Txn.last_valid`** — the validity window bounds replay; an unbounded or far-future window widens the replay surface.
- **PyTeal:** `Gtxn[i].sender()`, `Gtxn[i].amount()`, `Txn.group_index()`, `Global.group_size()`. **Algorand Python:** `Gtxn[i].sender`, `Txn.group_index`, `Global.group_size`.

## Attack plan

1. Enumerate every `Gtxn[i]` / `gtxn*` read and the field(s) taken from it.
2. Check the index: is it the contract's relative position, or a fixed slot the attacker can occupy by reordering the group?
3. For each field, ask what validates it. If nothing does, craft a sibling that satisfies the numeric/size checks but carries an attacker-controlled `sender`, `receiver`, or `asset`.
4. Missing `group_size` check: submit the contract call alone in a 1-transaction group and see whether the multi-transaction assumption still holds.
5. Fee pooling: set the contract's `fee` to 0 and let another member pay; if the logic depends on the fee, this bypasses it.
6. Group replay: re-submit a previously accepted group. `Txn.lease` (a 32-byte anti-replay value) and `first_valid`/`last_valid` are the defenses; a missing lease permits replay of a value-moving group.
7. Amount/receiver confusion: send 0 or a tiny amount, or redirect the receiver, and check whether the contract still credits the expected accounting.
8. Reorder the group so the contract lands at the index it *thinks* a sibling occupies, and confirm the read still succeeds.

## Proof

- AlgoKit localnet + `pytest`: build the full malicious group with `algorand.new_group()` / `TransactionComposer` and submit it.
- Assert the unauthorized effect: a wrong `receiver` credited, a 0-fee sibling accepted, or a 1-transaction group passing a multi-transaction path.
- Compare against the intended group layout in the test log; the finding names the exact index and the unvalidated field.

```python
group = algorand.new_group()
group.add_app_call_method_call(app_client.params.my_method(...))
group.add_payment(PaymentParams(sender=attacker.addr, receiver=attacker.addr,
                                amount=AlgoAmount(micro_algo=0)))
result = group.send()   # assert the contract acted on the sibling it should not have
```

- A working PoC upgrades a lead to a finding; an unreachable or untested read is only a **lead**.
- Submit the same group with and without the malicious sibling and show the contract behaves differently only because the field is unvalidated; that difference is the finding.

## Fix

Assert `Global.group_size` and derive sibling indices from `Txn.group_index`; validate every `Gtxn[i]` field (`type_enum`, `sender`, `receiver`, `amount`, `xfer_asset`, `application_id`, `on_completion`); require the exact receiver/amount/asset the logic needs; bind the group with `Txn.group_id` (and check `Txn.tx_id` for a specific sibling) and set `Txn.lease` to prevent replay; never authorize on `Txn.fee`. See `ecosystems/algorand`, `tooling/algorand`, `hacking_agents/execution-trace`.

## See also

- `ecosystems/algorand` — AVM model, group and inner-txn semantics.
- `tooling/algorand` — localnet and the `pytest` group harness.
- `vulnerabilities/algorand-account-and-rekey`, `vulnerabilities/algorand-inner-and-storage` — sibling AVM surfaces.
- `hacking_agents/execution-trace`, `hacking_agents/asymmetry` — parameter divergence and index mismatches.
