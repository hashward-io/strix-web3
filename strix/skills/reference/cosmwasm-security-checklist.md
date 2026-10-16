---
name: cosmwasm-security-checklist
description: CosmWasm security checklist — address canonicalization, attached funds, submessage/reply state machine, queries, migration and admin
---

# CosmWasm Security Checklist

A checklist for reviewing CosmWasm contracts (`cosmwasm-std`, `cw-*`) and Cosmos SDK modules. The trust boundaries are **address canonicalization**, **attached funds**, and the **submessage/reply** state machine. Distilled from the CosmWasm docs and public audit findings.

## Addresses & funds

- [ ] **Uncanonicalized address** — comparing `info.sender` (an `Addr`) to a stored string, or trusting a human bech32 form across chains. Prevent: store/compare `Addr`, use `deps.api.addr_validate` on user input (`vulnerabilities/cosmwasm-address-and-funds`).
- [ ] **Attached funds unverified** — `execute` uses `info.funds` without asserting the denom, amount, or that exactly one coin was sent. Prevent: validate `info.funds` against the expected denom and amount.
- [ ] **Funds sent to the wrong recipient** — a `BankMsg::Send` to a caller-supplied address, or refunds to `info.sender` when funds came from elsewhere.
- [ ] **cw20 `TransferFrom` semantics** — a cw20 token uses `send`/`transfer_from` where an `Allowance`/`Expiration` check is assumed.

## Messages & replies

- [ ] **Reply id confusion** — `reply` dispatches on `msg.id` but ids collide, are off-by-one, or are reused across message types (`vulnerabilities/cosmwasm-message-and-reply`).
- [ ] **Trusting the submessage result** — acting on a `SubMsgResult` without matching the expected `Ok` payload, or treating an errored reply as success.
- [ ] **`reply_on_success` vs `reply_always`** — erroring submessage state assumed to have been rolled back when it was not.
- [ ] **Submessage ordering** — assuming submessages execute before code later in the same `execute`; they run after the current message returns.

## Queries

- [ ] **Spoofable external query** — trusting `deps.querier.query_wasm_smart` against a contract address that is not pinned/whitelisted (the queried contract is attacker-controlled).
- [ ] **Stale or manipulated price query** — using a queried price without a freshness/validity check.

## Migration, admin & code

- [ ] **Unprotected migration** — `MigrateMsg` not gated on `info.sender == info.admin` (or the migration is irreversible / drops fields) (`vulnerabilities/cosmwasm-migration-and-admin`).
- [ ] **Admin unset or unchangeable** — `instantiate` leaves `admin` empty when it must not, or `UpdateAdmin` has no auth.
- [ ] **Instantiate front-running** — a contract that assumes it is the first/only instance, without a one-shot guard.

## Arithmetic & limits

- [ ] **Overflow / divide-by-zero** — release builds wrap; use `checked_*` and `Uint128`/`Decimal` correctly (see `vulnerabilities/precision-rounding`).
- [ ] **Unbounded iteration** — looping over a growing map in `execute`, exceeding the gas/block limit.

## Validation

- [ ] Reproduce with `cw-multitest` (multi-contract) or `mock_dependencies`/`mock_info` — wrong `info.sender`, spoofed funds, a crafted submessage/reply sequence, or a bad migration, asserting the unauthorized state change.
- [ ] `cargo wasm32` build + `cosmwasm-check` on the artifact before trusting the deploy.
