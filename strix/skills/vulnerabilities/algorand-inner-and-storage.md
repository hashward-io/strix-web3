---
name: algorand-inner-and-storage
description: Algorand inner transactions and state - caller_app_id authorization, inner fee and sender control, box MBR and box ops, global vs local state exhaustion, ARC-4 decode
---

# Inner Transactions and State (Algorand)

A contract can create transactions of its own with `itxn_begin`/`itxn_field`/`itxn_submit`, and it owns boxes plus fixed global/local state. Inner transactions run with the app's authority, and boxes/state are funded by **MBR**, so both the fields of an inner txn and the way storage is created and funded are attack surface.

## Where to look

- **Inner transaction construction** — `itxn_begin` / `itxn_field` / `itxn_submit` / `itxn_next`; fields `Sender`, `Receiver`, `Amount`, `TypeEnum`, `Fee`, `ApplicationID`, `ApplicationArgs`, `Accounts`, `Assets`, `Applications`, `RekeyTo`, `CloseRemainderTo`.
- **`Global.caller_app_id` / `Global.caller_app_address`** — authorize an inner app call by the caller app id. `0` means the call is outer; for an inner call `Txn.sender` is the *calling app*, so a sender check verifies the wrong identity.
- **Inner fee** — an inner txn with `Fee == 0` draws its fee from the app's account (or the pooled group fee). An inner `Fee` copied from an app argument lets a caller drain the app account.
- **Inner sender** — `set_sender` / `itxn_field(Sender)` with an untrusted value can make the app spend from the wrong account; the sender must be the app itself unless deliberately delegated.
- **`Global.current_application_address`** — the app's own account; MBR and balances live here, and an inner txn with `Fee == 0` draws its fee from it.
- **`itxn` / `gitxn` / `itxna` reads** — `itxn` returns the field of the current or last-submitted inner transaction and `gitxn` indexes by inner-group position; a wrong index or a read before the field is set yields the wrong transaction's value.
- **Depth and budget** — app-call depth limit **8**; up to **256** inner txns per group; the opcode budget is **pooled** (700 per app call, +700 per inner app call at `itxn_submit`). An attacker can add sibling app calls to inflate the shared budget, or starve a path that assumes a fixed budget.
- **Boxes** — `box_create`, `box_extract`, `box_replace`, `box_del`, `box_len`, `box_get`, `box_put`; `Box`/`BoxMap`. MBR = `2500 + 400 * (name + size)` µALGO; name ≤ 64 bytes; each box referenced in the app call (≤ 8 references) must be declared.
- **Box bounds** — `box_extract`/`box_replace` must be bounds-checked against `box_len`; a missing length check reads past the stored box or reverts at an unexpected point.
- **State** — `app_global_get/put/del`, `app_local_get/put/del`, `App.globalGet`/`globalGetEx`/`localGet`. Global state ≤ 64 entries (8 KB), local ≤ 16 entries (2 KB), values ≤ 128 bytes, schema fixed at creation.
- **Cross-app reads** — `App.globalGetEx(app_id, key)` reads another app's global state; an untrusted `app_id` (from `Txn.applications`) makes the read attacker-controlled.
- **ARC-4 ABI** — `abi.encode`/`abi.decode`, `arc4.String`, `arc4.DynamicArray`, method selectors; assumptions about the length/offset prefixes of dynamic types.

## Attack plan

1. Enumerate every inner transaction and each field's source; flag any field taken from `Txn.application_args`, `Txn.accounts`, `Txn.assets`, or `Txn.applications`.
2. Copy an untrusted value into inner `Sender`, `Fee`, `RekeyTo`, or `CloseRemainderTo` and show the app acts on it.
3. Authorize an inner app call by `Txn.sender` instead of `Global.caller_app_id` and call the app directly (outer), or the reverse.
4. Grief MBR: drive a path that creates boxes or opts accounts in with attacker-chosen names/sizes, draining the app account's MBR until operations fail.
5. Exhaust state: fill global (64) or local (16) slots so a later write aborts.
6. Feed `App.globalGetEx` an attacker-supplied `app_id` and observe the read.
7. Decode malformed ARC-4 bytes (bad length/offset) into a value the contract trusts.
8. Submit a group with extra sibling app calls to inflate the pooled opcode budget and reach a path a fixed-budget assumption rejected.
9. Read `itxn`/`gitxn`/`itxna` with a mismatched inner index and confirm the field comes from the wrong inner transaction.

## Proof

- AlgoKit localnet + `pytest`: assert the app account's balance drops after an inner-txn fee/sender attack, or that box creation increased MBR with an attacker-chosen key.
- Show a state write reverting after exhausting the schema; assert the exact entry count via `app_client.state.global_state.get_all()`.
- For `globalGetEx`, deploy a second app with a forged value and show the first app reads it.
- For ARC-4, pass a hand-built byte string and prove the decoded value diverges from the encoded intent.

```python
before = algorand.account.get_information(app_address).amount
app_client.send.create_box(name=b"attacker_chosen", size=32768)
after = algorand.account.get_information(app_address).amount
assert before - after >= 2500 + 400 * (len(b"attacker_chosen") + 32768)   # MBR griefed
```

## Fix

Construct inner transactions with constant, validated fields; never copy `Sender`, `Fee`, `RekeyTo`, or `CloseRemainderTo` from caller input; set the inner sender to the app (`Global.current_application_address`) and pin `Fee`. Authorize inner app calls with `Global.caller_app_id`/`caller_app_address`. Charge and check box/state MBR explicitly, cap names and sizes, and reject box creates that exceed a budget. Bound `App.globalGetEx` to an allowlisted app id. Validate ARC-4 lengths/offsets before decoding. See `ecosystems/algorand`, `tooling/algorand`, `vulnerabilities/access-control`, `hacking_agents/boundary`.

## See also

- `ecosystems/algorand` — inner-txn, box, and MBR model.
- `tooling/algorand` — localnet `pytest` harness for boxes and state.
- `vulnerabilities/algorand-group-transactions`, `vulnerabilities/algorand-account-and-rekey` — sibling AVM surfaces.
- `hacking_agents/boundary`, `hacking_agents/flow-gap` — state limits and cross-call value seams.
