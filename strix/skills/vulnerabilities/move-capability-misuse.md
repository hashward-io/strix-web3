---
name: move-capability-misuse
description: Move capability and authority misuse - missing Cap requirements, copyable/freezable caps, one-time-witness misuse, friend leakage, Publisher trust, admin cap transfer
---

# Capability & Authority Misuse (Move)

Move has no ambient authority: a privileged action must consume a capability value — an
`AdminCap`/`&TreasuryCap` object, a `Publisher`, an Aptos `SignerCapability`, or a one-time
witness. A capability that is forgeable, unused, freely transferable, or issued to the wrong
holder collapses the whole permission model.

## Where to look

- **Functions that never take the Cap** — a `public fun mint` / `public entry fun set_fee` whose
  parameter list omits the `&mut AdminCap` / `&TreasuryCap` / `cap: &Cap`. The check must be a
  type in the signature (or an explicit `assert!(cap.id == ...)`), not a comment.
- **`has copy` / `drop` on a cap struct** — a capability declared `has copy` can be duplicated;
  `drop` alone is harmless but `copy + drop` lets it be cloned and destroyed. Caps should be
  `key` only (object) or `key, store` if transfer is intended — evaluate whether `store` is safe.
- **`public_transfer` / `public_share_object` on a cap** — `sui::transfer::public_transfer` and
  `public_share_object` accept any `T: key + store`; exposing them for a cap type lets anyone who
  obtains the object relocate it. Prefer module-internal `transfer::transfer`.
- **One-time witness (OTW) misuse** — Sui derives `Publisher` and treasury mint authority from the
  OTW: a struct named exactly like the module in UPPERCASE, with only `drop`, no fields, and
  consumed by `sui::package::claim` / `sui::types::is_one_time_witness`. Wrong shape (extra
  fields, `store`, wrong name) or a public constructor lets an attacker fabricate a `Publisher`.
- **`Publisher` trust** — `publisher.claim<T>()`, `sui::package::from_package`, and
  `package::from_module`; verify the module proves provenance (the OTW) rather than trusting a
  publisher object passed in. A `Publisher` grants display/metadata/coin-registration control.
- **`friend` leakage** — `friend other::module;` grants full access to `public(friend)` and, in
  older Move, private items. A friend that is attacker-deployable (or any module) can call admin
  entry points. Each `friend` line is an attack surface.
- **Aptos `SignerCapability`** — `aptos_framework::account::create_resource_account` returns a
  `SignerCapability`; storing it in a publicly readable resource, returning it from a `public`/
  `#[view]` function, or failing to gate `signer_capability::account_address` usage lets anyone
  sign for the resource account.
- **Admin cap transfer / renounce symmetry** — `transfer::public_transfer(cap, new_owner)` with
  no allowlist, or a cap that can be swapped for a fresh one by an unprivileged caller.

## Attack plan

1. Enumerate every privileged function and confirm a capability type appears in its signature.
2. Inspect each cap struct's abilities: does `copy`/`store` allow duplication or theft.
3. For Sui, trace the OTW from module init to `package::claim`; check its shape and name.
4. For Aptos, trace `SignerCapability` creation, storage, and every read site.
5. List every `friend` declaration and ask whether the friend can be deployed by an attacker.

## Proof

- Sui: `sui move test` with a test in another module (or a `#[test]` module) that calls the admin
  function without the cap, or fabricates the witness. Use
  `#[expected_failure(abort_code = ...)]` to assert the correct rejection and show the missing
  path succeeding.
- Aptos: `aptos move test` invoking the resource-account path without the stored capability.
- Package-level: `sui move build` with an added `friend` to demonstrate the cross-module call.

```move
#[test]
fun attacker_calls_admin() {
    // no AdminCap passed; call succeeds => missing capability check
    set_fee(&mut ctx);
}
```

## Fix

Require the capability as a by-value/borrowed parameter for every privileged function; give caps
only `key` (no `copy`); never expose `public_transfer`/`public_share_object` for a cap; consume and
validate the OTW; gate on `Publisher` provenance; minimize and review `friend` declarations.
See `ecosystems/move`, `tooling/move-cli`, `vulnerabilities/move-visibility-and-friends`.
