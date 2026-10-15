---
name: ton-cell-and-gas
description: TON cells and gas — 1023-bit/4-ref/1023-depth limits, gas forwarding, storage rent, send_raw_message modes, commit(), cell bombs, and null() handling
---

# TON Cells and Gas

TON stores everything in cells (a tree of bits and refs) and charges for every bit, ref, and message hop that is processed. A parser that trusts a body's size or depth, or a send whose mode is wrong, turns a normal operation into an out-of-gas abort, a locked contract, or a drained balance.

## Where to look

- Cell construction and parsing: `begin_cell()`, `store_slice`, `store_ref`, `~load_ref`, `~load_bits`, `cell_depth`, `compute_data_size`.
- Dictionaries: `udict_set_builder`, `dict_set`, `dict_get?`, `~load_dict`, and any loop that walks a dictionary's keys.
- Outbound sends: `send_raw_message(msg, mode)`, `send_message`, and the mode constants `SEND_MODE_CARRY_ALL_REMAINING_MESSAGE_VALUE` (64), `SEND_MODE_CARRY_ALL_BALANCE` (128), `SEND_MODE_PAY_FEES_SEPARATELY` (1), `SEND_MODE_IGNORE_ERRORS` (2), `SEND_MODE_BOUNCE_ON_ACTION_FAIL` (16), `SEND_MODE_DESTROY_IF_ZERO` (32).
- Commit points: `commit()` and `accept_message()`.
- Storage economics: `storage_rent`, `due_payment`, and the config's `storage_rent` / `freeze_due_limit`.

## Limits and why they bite

- A single cell holds at most **1023 bits** and **4 refs**. Splitting data wrong silently drops a bit and corrupts a parsed value.
- Maximum **depth is 1023**. A contract that recursively parses refs without a depth or count bound accepts a "cell bomb": one tiny message whose ref tree forces the receiver to walk an enormous structure and run out of gas.
- Serialization must fit; an unbounded list appended into one cell throws at some element count — a griefing DoS in the deposit path.

## Attack plan

1. Enumerate every place a message body, forward payload, or stored cell is parsed. Ask: is the depth, ref count, or iteration length bounded? If not, build a deeply nested or wide cell and observe the abort.
2. Cell bomb: craft a message whose body is a chain or fan-out of refs. The receiver's parse loop exhausts gas before it can reject the message; if the message carries value, the abort is a bounce/refund, but the *processing* slot is consumed.
3. Send modes: a withdraw that uses mode 128 (`carry all balance`) forwards the whole contract balance rather than the requested amount. Mode 64 forwards the remaining message value, which may be tiny or huge depending on the caller.
4. Mode 2 (`ignore errors`) plus a bad destination silently destroys value; combined with a user-chosen destination, funds are lost.
5. Out-of-gas partial state: without `commit()`, a throw rolls back everything — good. But if the code `commit()`s mid-processing and later throws, the committed writes survive while the caller sees a failure, desynchronizing balances.
6. Storage rent: a contract that never maintains its balance gets frozen and its state deleted. A design that assumes persistent storage for free is a time-bomb DoS.
7. `null()` handling: `~load_dict` returns `null()` when absent; calling dict ops on a null dict can throw. A missing entry must be handled, not assumed present.

## Proof

- Sandbox PoC (`@ton/sandbox`, `npx blueprint test`): construct a cell bomb (nested refs) and assert the transaction aborts on gas.
- Compute `cell_depth` and bit/ref counts of an attacker-supplied body to show it exceeds the bound the code assumed.
- For send modes, show the contract balance before/after a withdraw and demonstrate over- or under-transfer.
- For commit/out-of-gas, dump state after the aborted transaction and show it diverged from the intended outcome.

## Fix

- Bound every parse: cap ref count, depth, and dictionary iteration; reject oversized or too-deep cells *before* the expensive walk.
- Serialize only what is needed; keep message bodies small and predictable.
- Choose send modes deliberately: `+1` to pay fees separately, `+16` to bounce on action failure, and avoid modes 64/128 unless forwarding the entire balance is the intent.
- Avoid `commit()` except where partial state must survive; prefer atomic all-or-nothing handling.
- Fund contracts for storage rent or document the freeze risk; treat persistent storage as a paid resource.
- Guard `null()` before dict/cell ops.

## Severity and finding bar

- A reachable out-of-gas abort on a value-carrying message is **Medium**; if it locks funds or bricks a shared entry point, **High**.
- A send-mode bug that over-forwards the contract balance (modes 64/128) and drains it is **Critical**.
- Storage-rent/freeze risk is **Medium** unless it is the only user exit path, then **High**.
- Committed partial state that diverges from the caller's view is **High** when funds are at stake.

## See also

- `ecosystems/ton` — the ecosystem playbook.
- `vulnerabilities/dos-griefing`, `vulnerabilities/accounting-conservation` — the general classes.
- `ton-sender-and-bounce`, `ton-jetton-and-getmethods` — sibling TON surfaces.
