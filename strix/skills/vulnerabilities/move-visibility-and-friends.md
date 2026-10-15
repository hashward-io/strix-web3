---
name: move-visibility-and-friends
description: Move visibility and friends - public(friend)/public(package), entry vs public, over-public functions, acquires/global storage, naming ambiguity, package upgrade policy
---

# Visibility, Friends & Upgrade Policy (Move)

Move's permission model is the visible surface of each module. A function that is too visible, a
`friend` that should not exist, or an upgrade policy that permits incompatible changes all expose
privileged logic that the author intended to keep internal.

## Where to look

- **`public` where it should be `public(friend)`/`public(package)`** — a state-mutating helper
  left `public`. In Sui, `public(package)` replaced `public(friend)` for package-internal access;
  on Aptos, `public(friend)` restricts to declared friends. Any function that mints, burns, sets a
  config, or moves funds must not be plain `public` unless global access is intended.
- **`entry` vs `public`** — `entry` makes a function callable directly from a transaction;
  `public entry` is both callable and composable. An `entry` function that bypasses an internal
  guard (e.g. calls the raw `_mint` instead of the checked `mint`) is a back door. Check every
  `entry`/`public entry` for the same invariants the front-door function enforces.
- **Functions that should be private** — `fun` (private) vs `public fun`. Helpers with no
  authorization that are `public` let anyone invoke them. Also check `#[test_only]` is not relied
  on for production guards.
- **`acquires` / global storage access** — Aptos `move_to`, `borrow_global`, `borrow_global_mut`,
  `move_from`, `exists<T>(addr)` and the `acquires T` effect annotation. A `public` function that
  `borrow_global_mut<T>(addr)` for a caller-supplied `addr` lets anyone mutate any account's
  resource. Sui's global storage analog is dynamic fields / shared objects (see
  `vulnerabilities/move-object-and-dynamic-fields`).
- **Ambiguous module / naming** — two modules or functions differing only by case/underscore,
  a public wrapper that shadows an internal name, or a function name (`transfer`, `mint`) that a
  consumer mistake for a framework one. Sui's `public(package)` visibility changes silently on a
  package upgrade — verify the effective visibility per version.
- **Package upgrade policy** — Sui publishes with an `upgrade_policy`: `compatible` (only
  compatible changes allowed after), `additive`, `dependency-only`, or `immutable`.
  `sui client publish --upgrade-policy compatible` still allows adding new public entry points and
  changing function bodies; `additive` allows adding but not changing; `immutable` forbids
  upgrade. On Aptos, `--upgrade-policy compatible`/`immutable`. An over-permissive policy means a
  later upgrade can alter logic behind a trusted address. Check the published policy against the
  protocol's trust claims.
- **`friend` declarations** — see `vulnerabilities/move-capability-misuse`; each `friend` is a
  grant of internal access.

## Attack plan

1. Build the visibility map: for every function, record `public` / `public(package)` /
   `public(friend)` / `entry` / private and its authorization requirement.
2. Cross-check each `public` function: is global access intended, or does a `friend`/package
   scope exist that should contain it?
3. For each `public entry` / `entry`, verify it enforces the same checks as the composable path.
4. On Aptos, list every `public` function that touches `borrow_global_mut` with a caller address.
5. Read `Move.toml` and the published `upgrade_policy`/edition; decide if a future upgrade can
   break a consumer's assumptions.

## Proof

- Sui: `sui move test` calling a function from a module that is neither a friend nor the same
  package — the compiler rejects it if visibility is correct. If it compiles and a test can call
  it, the surface is public.
- Aptos: `aptos move test` with a `borrow_global_mut` under a caller-supplied address.
- Upgrade: `sui client publish --upgrade-policy <policy>` (on a local `sui start`/testnet) then
  `sui client upgrade` with a changed function body; show the upgrade is accepted where the
  protocol claims immutability.

```move
// compiles from an unrelated module => visibility too broad
public fun set_fee(new_fee: u64) { /* no cap, no friend */ }
```

## Fix

Narrow visibility to the minimum (`fun`, `public(package)`, `public(friend)`); never leave
privileged mutation plain `public`; make `entry` wrappers enforce the same guards as the
composable path; audit `acquires`/`borrow_global` for caller-controlled addresses; choose the
strictest viable `upgrade_policy`. See `ecosystems/move`, `tooling/move-cli`.
