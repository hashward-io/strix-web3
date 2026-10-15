---
name: upgradeability-proxy
description: Proxy and upgrade risks — storage collisions, uninitialized implementations, unsafe upgrades, delegatecall context, and initializer front-running
---

# Upgradeability and Proxies

A proxy separates logic from storage. Every seam is a place where the upgrade can corrupt state.

## Where to look

- **Storage layout collisions.** A new implementation that inserts, reorders, or retypes a storage variable shifts every slot below it — corrupting existing state. Check for a `__gap` on base contracts and an explicit layout (`ERC-7201` namespaced storage is safest).
- **Uninitialized implementation.** The logic contract behind the proxy is usually left uninitialized so `delegatecall`s work; but if an attacker can call `initialize()` **directly on the implementation**, they can take it over. Guard implementations with `_disableInitializers()`.
- **Initializer front-running.** A proxy deployed and initialized in two transactions can be front-run: an attacker calls `initialize()` first and becomes owner. Deploy and initialize atomically (factory) or use `initializer` with a deployer check.
- **`initializer` / `reinitializer` versioning.** `reinitializer(n)` must strictly increase; a gap allows re-running an init. `onlyInitializing` vs `initializer` misuse.
- **`delegatecall` context.** The implementation runs with the proxy's storage, `msg.sender`, and `address(this)`. Any logic that assumes `address(this)` is the implementation, or reads `immutable`/`constant` state set at implementation-deploy time, behaves wrong behind a proxy (`immutable` is baked into the implementation's bytecode, not storage).
- **Unsafe upgrade path.** `upgradeTo` without `onlyOwner` or a timelock; an upgrade function that is `external` and public; a UUPS proxy whose `_authorizeUpgrade` is empty.
- **Function selector collisions.** A proxy's own functions colliding with an implementation's (e.g. `upgradeToAndCall` reachable through the fallback).
- **`selfdestruct` / `delegatecall` to attacker-controlled target** in the implementation.
- **Constructor vs initializer.** State set in the implementation's constructor is not visible through the proxy (it lives in the implementation's storage, not the proxy's).

## Attack plan

1. Identify the proxy pattern (Transparent, UUPS, Beacon, Diamond) and where storage starts.
2. Diff old vs new storage layout on any upgrade in scope.
3. Check the implementation for a live `initialize` and whether it is disabled.
4. Check the authorization on the upgrade function.
5. Check every `immutable`/`constant`/`address(this)` assumption against delegatecall semantics.

## Proof

For an uninitialized implementation or a front-runnable initializer, show the takeover call. For a layout collision, show the read after upgrade returning corrupted state.

## Fix

Use ERC-7201 namespaced storage with `__gap`s; `_disableInitializers()` in the implementation constructor; deploy-and-initialize atomically; `onlyOwner`/timelock + `_authorizeUpgrade`; run storage-layout checks (`forge inspect ... storageLayout`) in CI.
