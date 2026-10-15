---
name: sway-arithmetic-and-reentrancy
description: Sway arithmetic and reentrancy — overflow modes (error-on-overflow vs wrapping), AssetId/msg_sender checks, msg_amount vs this_balance, and external-call reentrancy
---

# Sway Arithmetic and Reentrancy

Sway compiles with overflow checks depending on flags, distinguishes assets by `AssetId`, and has no built-in reentrancy guard. A wrapped subtraction, a missing asset-id check, or a state update after an external call is the difference between a safe contract and a drained one.

## Where to look

- Arithmetic: `+`, `-`, `*`, `add`, `sub`, `mul` (panicking) versus `wrapping_add`, `wrapping_sub`, `overflowing_*`. Build flags `--error-on-overflow` (and whether `--release` disables checks).
- Asset identity: `msg_asset_id()`, `this_balance(asset_id)`, `asset_balance_of`, and any comparison of `AssetId` (the native asset is `AssetId::zero()` / the base asset, so a zero-id check can be a foot-gun).
- Caller and value: `msg_sender()` (a `Result<Identity, ...>` — note it is fallible for contracts), `msg_amount()` (value attached to *this* call), versus `this_balance()` (the contract's total balance).
- External calls: `abi(Other, other_id)`, `other.method()`, and the `#[payable]` annotation on the abi method. Any call that hands control to another contract.
- Context: `#[payable]` on an abi function to receive the base asset; scripts and predicates do not have storage or `msg_sender` semantics the way contracts do.

## Attack plan

1. Determine the build profile: is overflow checking on? In release builds without `--error-on-overflow`, `+`/`-`/`*` wrap silently. A subtraction that can underflow then produces a huge `u64` and passes a later `<= balance` check.
2. Hunt underflows: `balance - amount` with a caller-influenced `amount`, `a - b` where the code "knows" `a >= b` but only proves it elsewhere. A wrap mints balance.
3. `AssetId` confusion: a function that should operate on one asset but uses a caller-supplied `asset_id`, or treats `AssetId::zero()` (the native asset) as "no asset". Deposit/withdraw with the wrong id can drain the base asset or a mock token.
4. `msg_amount` vs `this_balance`: code that checks `msg_amount()` for a withdraw but pays from `this_balance()` — or vice versa — mixes "how much this call attached" with "how much the contract holds". A tiny `msg_amount` can authorize a large `this_balance` payout.
5. `msg_sender()` unwrap: it returns a `Result`; `unwrap()` reverts for contract callers. Check authorization uses the recovered `Identity` and compares it to the owner.
6. Reentrancy: a `#[payable]` / fund-moving method that calls an external contract *before* updating its own state. The callee re-enters (or a callback in `receive`/`fallback`), reads the stale balance, and withdraws again. Sway provides no reentrancy lock.
7. Context mismatch: logic valid in a contract (`msg_sender`, storage) copied into a script or predicate where those do not hold, producing an unsatisfiable or trivially-satisfiable predicate (see `sway-storage-and-predicates`).

## Proof

- `forc test` with `#[test]` and the Sway test framework, or `fuels-rs` / `fuels-ts` integration on a `forc build`-ed contract; assert the wrapped-underflow mint or the drained balance.
- Build with and without `--error-on-overflow` and show the behavioral divergence.
- For reentrancy, deploy two contracts where the callee re-enters the caller mid-call; show the double spend.
- For asset confusion, deposit the wrong `AssetId` and show the withdrawal.

## Fix

- Build with `--error-on-overflow`, or use explicit `checked_*` / `overflowing_*` with handled results; never rely on a non-negative "obvious" subtraction.
- Pin the `AssetId` in every value path; reject caller-supplied ids unless explicitly allowed, and handle the native-asset id deliberately.
- Compare `msg_amount()` to the requested amount for deposits and use `this_balance()` only for the actual payout; keep the two roles distinct.
- Handle the `msg_sender()` `Result` explicitly; deny by default when it is `Err`.
- Apply checks-effects-interactions; update state before external calls; add a reentrancy guard (an explicit storage flag) on all fund-moving entry points.

## Overflow and asset quick reference

- `--error-on-overflow` forces panics on overflow for `+ - *`; without it (or in release) they wrap.
- `checked_*`, `saturating_*`, `overflowing_*`, `wrapping_*` are always available and explicit.
- `msg_asset_id()` is the asset attached to the current call; `this_balance(id)` is the contract's total.
- The base asset has a fixed `AssetId`; comparing it to `AssetId::zero()` is a common mistake.
- `msg_sender()` returns `Result<Identity, ...>`; handle the `Err` (contract callers).

## Severity and finding bar

- A wrapped underflow that mints balance or bypasses a check is **Critical**.
- A missing `AssetId` check that lets one asset drain another is **High** to **Critical**.
- `msg_amount`/`this_balance` confusion enabling over-payout is **Critical**.
- Reentrancy that double-spends is **Critical**; a missing guard on a non-value path is **Low**.

## See also

- `ecosystems/sway` — the ecosystem playbook.
- `vulnerabilities/reentrancy`, `vulnerabilities/precision-rounding` — the general classes.
- `sway-storage-and-predicates` — the sibling Sway surface.
