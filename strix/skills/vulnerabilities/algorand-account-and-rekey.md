---
name: algorand-account-and-rekey
description: Algorand sender, rekey and close bugs - unchecked Txn.sender or caller_app_id, missing asset/app allowlists, rekey takeover, close-remainder drain, clawback trust
---

# Sender, Rekey and Close (Algorand)

On Algorand an action is authorized by `Txn.sender`, and an account's *entire* control can be handed to another key with a single **rekey**. A contract that misreads the sender, ignores `Global.caller_app_id`, or fails to reject `close_remainder_to` and `rekey_to` can have funds drained or authority silently transferred.

## Where to look

- **`Txn.sender`** — must equal the stored admin/owner (`Global.creator_address` only for the creator). A state-changing path with no sender check is public.
- **`Global.creator_address` / `Global.current_application_address`** — creator-only is not an owner check, and authority that "comes from the app" must be tied to the app address, not to `Txn.sender`.
- **`Global.caller_app_id` / `Global.caller_app_address`** — when authorizing an inner app call, check the caller *app id*; `0` means the call came from an outer transaction. Authorizing an inner call by `Txn.sender` is wrong, because for an inner call the sender is the calling app's address.
- **`Txn.rekey_to`** — an app-call transaction can rekey its sender after execution. A contract should reject `Txn.rekey_to != Global.zero_address` unless rekeying is the intent; an inner `set_rekey_to` copying an untrusted value is full takeover.
- **`Txn.close_remainder_to` / `Txn.asset_close_to`** — a payment or asset transfer can close the account, moving every remaining µALGO/asset out.
- **`Txn.asset_sender` (clawback)** — for an ASA with a clawback address, the clawback holder can move assets from *any* account. An asset id whose clawback is attacker-controlled must not be trusted.
- **Allowlists** — `Txn.assets` (foreign assets) and `Txn.applications` (foreign apps) let the caller attach arbitrary ids. If the contract operates on `Txn.assets[i]` without checking it is the expected asset/app, the attacker supplies their own.
- **`Txn.accounts`** — the foreign-account array; an index used as "the fee recipient" or "the vault" is attacker-chosen unless validated.
- **Opt-in / closeout** — `Txn.on_completion` (`OptIn`, `CloseOut`, `ClearState`); local state is deleted on closeout, and clear-state can be triggered by anyone. `Txn.application_args` (first is the ARC-4 selector) must be validated or method dispatch is bypassable.
- **Asset parameters** — `AssetParam.manager`, `.clawback`, `.freeze`, `.reserve`, `.default_frozen` read from an untrusted asset id.
- **App opt-in** — `Txn.on_completion == OptIn` is permissionless; state written at opt-in must be safe against an attacker who opts in and later closes out.

## Attack plan

1. For each state-changing method, identify the authorization field and prove it is checked: `Txn.sender == stored` or `Global.caller_app_id == expected`.
2. Where an inner app call is authorized, try calling the app directly (outer) with `Txn.sender` set to the expected app's *address* instead of its app id.
3. Attach your own asset/app via `Txn.assets`/`Txn.applications` and see whether the contract accepts it (clawback, freeze, spoofed parameters).
4. Pass a `rekey_to` you control on a path that trusts the field, and confirm the account is rekeyed to you.
5. Set `close_remainder_to` (or `asset_close_to`) and check whether the contract signs off on a full drain.
6. On a closeout/clear-state path, confirm local state is deleted and re-opt-in is possible with attacker-controlled state.
7. Route to an unintended method by forging `application_args[0]` if the selector is unvalidated.
8. Rekey to `Global.zero_address` on a legitimate path to confirm the check exists, then to the attacker to confirm it does not.

## Proof

- AlgoKit localnet + `pytest`: create the attacker ASA (clawback = attacker), pass it in `Txn.assets`, and show the contract spends it or reads its parameters.
- Rekey: submit an app call whose `rekey_to` is the attacker, assert the account's auth address changed, then move funds.
- Close: assert the victim's remaining balance is 0 after the call.
- Opt-in/closeout: opt in, trigger closeout, re-opt in, and assert the state reset.
- For allowlists, pass the *expected* asset id and a forged one and show the two paths behave differently.
- Also show the negative case (a zero-address rekey or close succeeds) so the missing check is unambiguous.

```python
group = algorand.new_group()
group.add_app_call_method_call(app_client.params.withdraw(asset=attacker_asa))
group.add_asset_transfer(...)   # attacker clawback moves the victim's units
group.send()                    # assert unauthorized transfer/state change
```

## Fix

Compare `Txn.sender` to the stored admin on every privileged path; authorize inner app calls with `Global.caller_app_id` (and `Global.caller_app_address`), not `Txn.sender`; reject `Txn.rekey_to` and inner `set_rekey_to` unless explicitly intended; require `Txn.close_remainder_to == Global.zero_address` (and `asset_close_to`) on payments you co-sign; allowlist asset/application ids and verify `AssetParam.clawback`/`freeze` before trusting an ASA; validate `Txn.on_completion` and the ARC-4 selector before dispatch. See `vulnerabilities/access-control`, `ecosystems/algorand`, `tooling/algorand`.

## See also

- `ecosystems/algorand` — sender, rekey, and close semantics in the AVM model.
- `tooling/algorand` — localnet harness for constructing these transactions.
- `vulnerabilities/access-control` — the chain-agnostic permission-model lens.
- `hacking_agents/access-control`, `hacking_agents/trust-gap` — authority misuse and confused-deputy seams.
