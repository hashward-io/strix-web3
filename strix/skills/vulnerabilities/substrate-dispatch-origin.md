---
name: substrate-dispatch-origin
description: Substrate and ink! dispatch origin — ensure_signed/ensure_root misuse, public-by-default messages, caller spoofing via proxies, and payable/weight gaps
---

# Substrate and ink! Dispatch Origin

Every dispatchable has an `origin`, and every ink! `#[ink(message)]` is publicly callable by default. Authorization exists only where the code asks for it — via `ensure_signed`/`ensure_root` in FRAME, or `self.env().caller()` in ink!. Getting the who-wrong, or assuming a message is private when it is not, is the classic escalation.

## Where to look

- FRAME dispatchables: `#[pallet::call]`, the `origin: OriginFor<T>` parameter, and the guard that consumes it — `ensure_signed`, `ensure_root`, `ensure_none`, or a custom `EnsureOrigin`.
- ink! messages: every `#[ink(message)]` is externally callable. Is there an explicit `assert_eq!(self.env().caller(), self.owner)` or an `only_owner` modifier?
- Identity type confusion: `Caller` (ink! 4) vs `AccountId` (ink! 5, `self.env().caller()` returns `AccountId`). A stored `Caller` compared to an `AccountId` can never match, silently disabling the guard.
- Payable and value: `#[ink(payable)]` / `#[ink(message, payable)]` and `self.env().transferred_value()`. A non-payable message rejects attached value; a payable one that ignores `transferred_value()` strands funds.
- Proxy and multisig trust: a contract called through a proxy or multisig sees the *proxy's* address as `caller()`. Any "is this the admin?" check based on `caller()` is spoofable by routing through the admin's proxy.
- Weight: `#[pallet::weight(...)]` / `#[pallet::call_index]`; an under-declared weight lets a caller consume more block weight than accounted.

## Attack plan

1. List every dispatchable / `#[ink(message)]` and classify: public-anyone, owner-gated, root-only. Find messages that mutate privileged state with no explicit guard.
2. Grep for `ensure_signed` / `ensure_root` and confirm the returned account is the one used downstream. A `let _ = ensure_signed(origin)?;` discards the signer — often a missing authorization.
3. For ink!, compare the guard's expected type against the actual `caller()` type. A `Caller`-vs-`AccountId` mismatch makes an equality check always false (deny-all DoS) or, if inverted, always pass.
4. Proxy/multisig: reach an owner-gated message through the owner's proxy or a multisig whose address is trusted. If the contract trusts `caller()`, the proxy address passes the check and the real user is unconstrained.
5. Constructor/initializer: is the owner set in `#[ink(constructor)]`? A default `AccountId::from([0u8;32])` owner or an unset owner is a takeover when the first caller becomes owner.
6. Payable: send value to a payable path that does not credit it, or reach a fund-moving path that a non-payable misconfiguration lets anyone call.
7. Weight: attach heavy input (large vectors, deep storage iteration) to an under-weighted dispatchable and show block-weight over-consumption (see `substrate-storage-and-weight`).

## Proof

- ink!: `cargo contract test` with `ink::env::test::set_caller::<Env>(acct)` to impersonate the proxy/admin, plus `ink_e2e` for real cross-contract calls. Assert the unauthorized mutation.
- FRAME: a runtime `cargo test` with `new_test_ext()` and `RuntimeOrigin::signed(...)` / `RuntimeOrigin::root()`.
- For caller spoofing, deploy a trivial proxy contract that forwards the call and show the guard passes.

## Fix

- Put an explicit guard on every privileged dispatchable; do not rely on a message "not being exposed".
- Use the value returned by `ensure_signed` / `ensure_root`; never discard it.
- Normalize identity: compare `AccountId` to `AccountId`; never mix `Caller` and `AccountId`. Store the owner and check it directly.
- Decide explicitly how proxies/multisig count as callers; prefer an `EnsureOrigin`/`ProxyType` mechanism over raw `caller()` equality.
- Initialize owner in the constructor and reject a default/zero owner.
- Mark messages `payable` only when value is consumed; read `transferred_value()` and account for it.
- Declare weight for the worst-case input, including storage reads/writes.

## Origin quick reference

- `ensure_signed(origin)` returns `T::AccountId`; `ensure_root(origin)` returns `()`. Both consume `origin`; reuse requires `origin.clone()`.
- `#[ink(message)]` has no default guard; `self.env().caller()` is `AccountId` in ink! 5 and `Caller` in ink! 4.
- Every FRAME `#[pallet::call]` dispatchable takes `origin: OriginFor<T>` as its first argument.
- `CallFlags::default()` vs `CallFlags::ALLOW_REENTRY` controls cross-contract reentrancy at the call site.

## Severity and finding bar

- An unguarded privileged mutation is **Critical** when it moves funds or replaces code, **High** otherwise.
- A caller-type mismatch that makes a guard deny-all is **Medium** (DoS); one that makes it pass is **Critical**.
- Proxy-based caller spoofing is **High** and needs a concrete forwarding POC.

## See also

- `ecosystems/substrate` — the ecosystem playbook.
- `vulnerabilities/access-control`, `vulnerabilities/upgradeability-proxy` — the general classes.
- `substrate-storage-and-weight`, `ink-storage-and-abi` — sibling ink! surfaces.
