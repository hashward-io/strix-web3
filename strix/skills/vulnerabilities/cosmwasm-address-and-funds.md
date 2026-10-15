---
name: cosmwasm-address-and-funds
description: CosmWasm addresses and funds — Addr vs String, addr_validate, info.funds vs BankMsg, native/cw20 confusion, Uint128/Decimal rounding, submessage reentrancy
---

# CosmWasm Addresses and Funds

CosmWasm separates the human-readable address (`String`), the validated `Addr`, and the canonical stored form. Funds arrive as a `Vec<Coin>` in `info.funds`, and sending them triggers receiver code. Each boundary is a bug surface.

## Where to look

- **Address canonicalization.** `deps.api.addr_validate(&input) -> StdResult<Addr>` validates the bech32 prefix and checksum and returns a canonical `Addr`; `deps.api.addr_canonicalize(&str)` gives the `CanonicalAddr`. Storing or comparing the raw `String` an attacker sent lets a wrong prefix, bad checksum, or mixed case differ from the real account.
- **`String` fields that should be `Addr`.** Grep struct fields typed `String` that hold addresses, and every `Addr` produced without `addr_validate`.
- **Case sensitivity.** Bech32 is case-insensitive but not mixed-case; two inputs can denote the same account while comparing unequal as `String`. Compare only after `addr_validate`/canonicalization, never stringly.
- **Prefix confusion.** A contract that accepts any bech32 prefix (not just the chain's) can treat a foreign-chain address as local.
- **Funds are not `msg.value`.** The attached coins live in `info.funds: Vec<Coin>`; a `<msg>.funds` field does not exist. You must assert the exact denom and amount the operation costs.
- **Missing / partial funds check.** A handler that ignores `info.funds`, or checks only one coin of several, accepts unpaid or overpaid calls.
- **`info.funds` vs `BankMsg::Send`.** `info.funds` is *inbound* native funds; `BankMsg::Send { to_address, amount }` is *outbound*. Confusing them (refunding while assuming funds arrived, or paying out from `info.funds` alone) lets an attacker drain or underpay.
- **Wrong denom.** Comparing `info.funds` against a denom the caller supplied, or trusting a denom string from the message, lets an attacker substitute a worthless coin.
- **Native vs cw20 confusion.** Native balances use `deps.querier.query_balance(addr, denom)`; CW20 balances use `cw20::query_balance(querier, token_contract, addr)` returning `BalanceResponse`. Treating a cw20 `amount` as native (or vice versa), or querying the wrong denom, misstates holdings.
- **Unvalidated token address.** A cw20 `token_contract` taken from a message and not `addr_validate`d, or not checked against a stored allow-list, points at an attacker token.
- **`Uint128` / `Decimal` rounding.** `Decimal` has 18 decimals (fixed); `Uint128` uses `checked_mul`, `checked_add`, `multiply_ratio`. `multiply_ratio` and `Decimal` division **truncate toward zero**; a round-trip (deposit/withdraw, mint/burn) can leak. Check the round direction of every `Decimal`↔`Uint128`↔raw conversion.
- **`Decimal` precision loss.** Multiplying two `Decimal`s loses the low 18 digits; chained operations drift. Prefer `multiply_ratio` for ratios.
- **`send` / `transfer` reentrancy via submessages.** A CW20 `Send { contract, amount, msg }` invokes the receiver's `ReceiveMsg`; a `BankMsg::Send` to a contract can trigger its logic. A `SubMsg` (not a plain `CosmosMsg`) waits for a `Reply` and runs receiver code **before** you finish — same class as EVM reentrancy.
- **State written after a `SubMsg`.** Any balance/config update after the submessage is inconsistent during the callback; re-enter and read it.
- **Duplicate coin entries.** `info.funds` may contain the same denom twice, or an empty `funds`; sum or reject as appropriate.

## Attack plan

1. Enumerate every address field and constructor; confirm each goes through `addr_validate` and is stored as `Addr`/`CanonicalAddr`.
2. For each payable entry, diff the accepted `info.funds` against what it should cost; try zero funds, wrong denom, and duplicate coins.
3. Trace value out: is the payout computed from `info.funds`, a queried balance, or internal state, and can they diverge?
4. Find every `SubMsg` (especially cw20 `send`); list the state written after it and re-enter.
5. For each `Decimal`/`Uint128` division, compute the truncation and test a round-trip.
6. Check every cw20/querier address is validated and stored.

## Proof

Use `cw-multitest` (`App`, `AppBuilder`, `app.execute_contract(...)`) to build a cw20 + victim and drive the wrong-case address, the missing funds check, or the submessage re-entry. A malicious receiver contract that re-enters the sender on `ReceiveMsg` is the gold-standard PoC. Show the balance delta and the trace from an unprivileged caller.

## Fix

Validate and store addresses as `Addr`/`CanonicalAddr`; never compare `String`. Assert the exact `info.funds` (denom and amount) for payable handlers. Separate inbound funds (`info.funds`) from outbound `BankMsg::Send`. Use `checked_*` and `multiply_ratio`, round in the protocol's favor, and normalize decimals. Avoid `SubMsg` when no reply is needed and apply checks-effects-interactions around any that remain.

## Variants and adjacent bugs

- **String-vs-`Addr` compare** — a case/prefix difference bypasses a check.
- **Missing funds check** — the handler runs with zero or wrong-denom funds.
- **cw20/native confusion** — the wrong balance source is read.
- **Truncating division** — `multiply_ratio`/`Decimal` round-trip leak.
- **cw20 `Send` reentrancy** — state written after the submessage callback.

## Do not flag

- Addresses validated with `addr_validate` and stored as `Addr`.
- Exact `info.funds` assertions for the required denom and amount.
- Fire-and-forget `CosmosMsg` sends with checks-effects-interactions.

## Leads vs findings

- A missing `addr_validate` or funds check is a **lead** until exploited.
- Prove with `cw-multitest` and a malicious receiver or a funds-delta trace.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/cosmwasm` — address, funds, and message model.
- `tooling/cosmwasm` — `cw-multitest` and build commands.
- `vulnerabilities/token-integration` — native and cw20 token pitfalls.
