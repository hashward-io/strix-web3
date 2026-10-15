---
name: cosmwasm-migration-and-admin
description: CosmWasm migration and admin — migrate version checks, admin transfer/renounce, instantiate re-init, cw2, self-calls, IBC callbacks, storage compatibility
---

# CosmWasm Migration and Admin

CosmWasm upgrades a contract by swapping its `code_id` while keeping storage. The runtime enforces none of the safety around that swap — version checks, storage compatibility, and IBC callback trust are all the contract's job.

## Where to look

- **`migrate` version checks.** `cw2::set_contract_version` / `get_contract_version(&deps.storage)` with `CONTRACT_NAME`/`CONTRACT_VERSION`. A `migrate` that does not assert the expected source version, or does not reject an unknown version, can be run from an incompatible or attacker-chosen predecessor.
- **Missing version guard pattern.** Look for `if info.version != CONTRACT_VERSION { return Err(...) }` (or an explicit per-version upgrade path) and flag its absence.
- **Migration writes without bounds.** A `migrate` that rewrites config/admin without re-validating values (e.g. writing an unvalidated admin address) hands over control.
- **Admin transfer / renounce.** The chain admin is set via `WasmMsg`/`SetContractAdminMsg` or at instantiate. An unaudited `UpdateAdmin`/`ClearAdmin` path, or contract logic reading a mutable "admin" field without `addr_validate`, lets ownership move. Renouncing (admin `None`) makes the contract immutable — verify it is intentional and not reachable by a non-admin.
- **Admin on the contract vs on the chain.** Some contracts store their own `admin: Addr` separate from the chain admin; the two can diverge, and a contract-level admin change may not affect who can call `migrate`.
- **Instantiate re-init.** `instantiate` must guard against pre-existing state: read `get_contract_version` and fail if the contract is already initialized, and only then `set_contract_version`. Otherwise an instantiate path (e.g. via a factory) can overwrite config or reset admin.
- **`cw2` metadata.** `cw2::set_contract_version` is the standard on-chain version tag; consumers (`cw2::get_contract_version` from a registry) trust it. A contract that never sets it, or sets it stale, misleads migration checks and registry logic.
- **Contract self-calls.** A `WasmMsg::Execute`/`SubMsg` pointed at the contract's own address re-enters its `execute` with a fresh message. Combined with a reply, this is reentrancy into migration or admin logic; check self-referential dispatch and whether it can reach privileged branches.
- **Proxy / registry trust.** A registry that stores member `contract_addr`s and forwards `WasmMsg::Execute` on their behalf, or a proxy holding a mutable implementation address, is only as safe as its trust in the caller. Validate the sender against the registered entry and never let the implementation address be set from user input.
- **IBC callbacks (`sudo`).** IBC-enabled contracts receive callbacks via `sudo` or the `ibc` entry points: `ibc_channel_open`, `ibc_channel_connect`, `ibc_channel_close`, `ibc_packet_receive`, `ibc_packet_ack`, `ibc_packet_timeout` (or `SudoMsg::Receive`/`Ack`/`Timeout`). The IBC module is the only sender, but the **data** from the remote chain is untrusted.
- **IBC channel binding.** If the contract does not bind the expected `channel_id`/`port_id` and local/remote channel, a spoofed or unexpected channel can drive state. Treat all packet payloads as attacker-controlled.
- **Upgrade storage compatibility.** `#[cw_serde]` field order matters: reordering or inserting fields corrupts reads of old data. Adding a field requires `#[serde(default)]` (or an explicit migration) or old entries fail to deserialize.
- **Type changes without migration.** Changing a field type (e.g. `Uint128` → `Decimal`) without a migration misreads balances.

## Attack plan

1. Read `migrate` end to end: source-version assertion, target-version write, and every storage field touched.
2. Check `instantiate` for an existing-version guard.
3. Trace the admin lifecycle: who can set, update, and clear it, and how the contract reads it.
4. Diff old vs new storage layout on any migration in scope; check `#[serde(default)]` and field order.
5. Inspect self-dispatch and registry/proxy forwarding for a re-entrant privileged path.
6. Enumerate IBC callbacks; confirm channel/port binding and payload validation.

## Proof

Use `cw-multitest`: `app.migrate_contract(sender, addr, msg, new_code_id)` to replay a bad version path, or instantiate twice through a factory to show state overwrite. For IBC, feed a crafted packet via the callback entry point and show the state change. For storage, write with code v1, migrate to v2, read the corrupted field. Show the concrete effect and the caller.

## Fix

Assert the expected source version in `migrate` and reject unknown ones; guard `instantiate` against existing state; always `set_contract_version`. Route admin changes through a validated, authorized path and document renounce semantics. Never let a proxy/registry implementation or member address be user-set. Bind IBC callbacks to the expected channel/port and validate remote payloads. Preserve field order and add `#[serde(default)]` or an explicit migration for new fields.

## Variants and adjacent bugs

- **Missing `migrate` version check** — run from an incompatible predecessor.
- **Re-initializable `instantiate`** — state/config overwrite via a factory.
- **Unaudited admin change** — unvalidated or unguarded transfer/renounce.
- **Unbound IBC callback** — spoofed channel/port or unvalidated packet.
- **Incompatible storage** — field reorder/insert/type change without a migration.

## Do not flag

- `migrate` that asserts the source version and writes the target version.
- Admin changes gated to the validated chain admin.
- IBC callbacks bound to the expected channel/port with payload validation.

## Leads vs findings

- A missing version/storage check is a **lead** until a corrupted read or takeover is shown.
- Prove with `cw-multitest` (`migrate_contract`) or a crafted IBC packet.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/cosmwasm` — migration, admin, and IBC model.
- `tooling/cosmwasm` — `cw-multitest` and build commands.
- `vulnerabilities/upgradeability-proxy` — storage compatibility.
