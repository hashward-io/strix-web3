---
name: algorand
description: Algorand AVM playbook - Algorand Python (Puya), PyTeal and Beaker; atomic groups, inner transactions, rekey, boxes and MBR, ARC-4/ARC-56, AlgoKit localnet
---

# Algorand Ecosystem

Algorand smart contracts are on-chain **AVM** programs with separate approval and clear-state programs. State lives in global/local state and **boxes**; the runtime's distinctive model — **atomic transaction groups**, **inner transactions**, **rekeying**, and the **minimum balance requirement (MBR)** — drives most AVM bugs.

## When to use

- An AlgoKit project (`algokit` CLI, `.algokit.toml`), `smart_contracts/`, or an ARC-56 app spec.
- Python sources importing `algopy`, `pyteal`, or `beaker`, or `.teal` assembly.
- Code using `Gtxn`, `itxn`, boxes, `App.globalGetEx`, rekey/close fields, or ASA/clawback logic.
- You need the AVM bug-class map before narrowing to `vulnerabilities/algorand-*`.

## Detecting the target

- AlgoKit config: `.algokit.toml` / `algokit.toml`, an `algokit project` workspace, `algokit` in scripts/CI.
- Algorand Python (Puya): `*.py` importing `from algopy import ...`, `@arc4.abimethod`, `@arc4.baremethod`, `@subroutine`.
- PyTeal: `*.py` importing `from pyteal import ...` (`Txn`, `Gtxn`, `InnerTxnBuilder`, `Router`).
- Beaker (legacy): `*.py` importing `beaker` (`Application`, `@external`, `@internal`).
- TEAL: `*.teal` approval/clear programs.
- App spec: `application.json`, `<Name>.arc56.json` (ARC-56), ARC-32 `.json`; `deploy_config.py` / `deploy-config.ts`; `smart_contracts/artifacts/`.

## Contract models

- **Algorand Python (`algopy`, PuyaPy compiler):** `Contract` / `arc4.ARC4Contract`; ABI methods `@arc4.abimethod`, bare methods `@arc4.baremethod`, helpers `@subroutine`. Typed `Global`, `Txn`, `Gtxn`, `itxn`, `Box`, `BoxMap`, `GlobalState`, `LocalState`.
- **PyTeal:** a `Router`/`@router` or a hand-built `Seq`; `Txn`, `Gtxn`, `App`, `InnerTxnBuilder`.
- **Beaker:** PyTeal framework with `@external`/`@internal`/`@opt_in` handlers (archived).
- **TEAL:** every check is explicit — audit opcode by opcode.

## The AVM security model

- An app call is one txn in a **group** of up to 16; the group is atomic (all succeed or all fail).
- `Txn.group_index` is your position; `Gtxn[i]` (`gtxn`/`gtxns`) reads siblings. Nothing guarantees a sibling's type, sender, or amount.
- **Fee pooling:** the group's fees sum; any one txn may pay all, so a valid member can carry `fee == 0`.
- **Inner transactions** (`itxn_begin`/`itxn_field`/`itxn_submit`, `itxn_next`) create txns; call depth **8**, up to **256** inner txns per group, opcode budget **pooled** (700 per app call, +700 per inner app call).
- **Rekey** (`Txn.rekey_to`, inner `set_rekey_to`) hands full account control to another key.
- **Boxes** are app-owned key/value storage with MBR `2500 + 400 * (name + size)` µALGO, name ≤ 64 bytes, size ≤ 32,768 bytes.
- **Global state** ≤ 64 entries / **local state** ≤ 16 entries; keys ≤ 64 bytes, values ≤ 128 bytes, schema fixed at creation.

## Where the bugs live

- **Group composition** — trusting a grouped txn's type/fields/sender; missing size/index checks; fee pooling; field (amount/receiver/asset) not validated. See `vulnerabilities/algorand-group-transactions`.
- **Sender / rekey / close** — unchecked `Txn.sender` / `Global.caller_app_id`; missing `Txn.assets`/`Txn.applications` allowlists; `Txn.rekey_to` takeover; `Txn.close_remainder_to` drain; clawback/`asset_sender` trust; opt-in/closeout. See `vulnerabilities/algorand-account-and-rekey`.
- **Inner txns & storage** — authorizing inner app calls by `Global.caller_app_id`; missing inner fee/sender controls; depth/opcode-budget pooling; box MBR and ops; state exhaustion; `App.globalGetEx`; ARC-4 encode/decode. See `vulnerabilities/algorand-inner-and-storage`.

## Toolchain & build

- AlgoKit CLI: `algokit init`, `algokit localnet start`, `algokit compile python`, `algokit deploy`, `algokit goal`.
- Localnet runs algod + kmd + indexer in Docker; `goal` drives node/account/app operations.
- PuyaPy compiles Algorand Python and emits the app spec (ARC-32/ARC-56); ARC-4 is the on-chain ABI (4-byte method selectors plus tuple encoding).
- See `tooling/algorand` for the full command reference.

## Proof standard

An **AlgoKit localnet** plus `pytest` using `algokit-utils` (`AlgorandClient`, typed app clients / `ApplicationClient`): build the malicious group, submit it, and assert balances, global/local state, and box contents. A bare code read is a **lead**; the confirmed finding names the exact group layout and the missing check. See `tooling/algorand`.

## Testing

- `algokit localnet start`, then `pytest tests/`; fixtures build an `AlgorandClient.default_localnet()`.
- Construct atomic groups explicitly (`algorand.new_group()` / `TransactionComposer`) to reproduce composition, fee, and rekey bugs.
- Read state back with `app_client.state.global_state` / `local_state` / `box`; check balances before and after.
- Use `algorand-python-testing` (AVM unit tests) for single-program logic without a node.

## Fix patterns

Validate every `Gtxn[i]` field (type, sender, receiver, amount, asset, app id); assert `Global.group_size` and `Txn.group_index`/`group_id`; never let a group member's `Fee`/`Sender`/`RekeyTo` be attacker-controlled; authorize inner app calls via `Global.caller_app_id` and pin inner `Sender`/`Fee`; bound `App.globalGetEx` and box reads; fund MBR explicitly; dispatch ARC-4 methods by a verified selector. See `vulnerabilities/algorand-group-transactions`, `vulnerabilities/algorand-account-and-rekey`, `vulnerabilities/algorand-inner-and-storage`, and `hacking_agents/access-control`.
