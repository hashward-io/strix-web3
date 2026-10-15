---
name: cairo-access-and-upgrade
description: Cairo/Starknet access control and upgrades — ContractAddress guards, external(v0) visibility, replace_class authorization, initializer and Ownable pitfalls
---

# Cairo Access Control and Upgrades

Cairo makes it easy to expose a component's admin interface by accident and to replace a contract's class with no storage-layout check. Map the permission surface, then attack every gap and every initializer.

## Where to look

- **`ContractAddress` guards.** Authorization usually compares `get_caller_address()` against a stored `ContractAddress`. Check it compares the caller (not `get_contract_address()`), that the stored address was initialized, and that `Zeroable::zero()` cannot satisfy it.
- **Owner / role checks.** OZ `OwnableComponent` exposes `ownable.owner()`, `assert_only_owner()`, `transfer_ownership`, `renounce_ownership`, and `initializer(new_owner)`. Every privileged function must call `assert_only_owner()` (or the role check).
- **Missing guard on one of several writers.** For a storage variable written by 2+ functions, find the weakest guard. If `set_fee` is owner-gated but `set_admin` is not, use `set_admin`.
- **`#[external(v0)]` visibility.** Functions inside an `#[external(v0)] impl` block are callable by anyone; functions outside it are not external. A privileged helper placed inside the external impl is exposed. Diff the ABI against intent.
- **`#[abi(embed_v0)]` exposure.** Embedding a component's interface publishes its entry points to everyone. Embedding `UpgradeableComponent` or a role-admin component without a matching in-component owner check hands over admin.
- **`replace_class_syscall` / `upgrade`.** `replace_class_syscall(class_hash)` swaps the class with **no storage-layout check**. OZ `UpgradeableComponent::upgrade(new_class_hash)` must be owner-gated and should validate the new class (allow-list, version, or a provable `ClassHash`). An unguarded or public `upgrade` is **Critical**.
- **Unvalidated `new_class_hash`.** Even owner-gated, an `upgrade` that accepts any class hash lets a compromised owner (or a mis-set owner) install arbitrary logic. Check for an allow-list / timelock.
- **Initializer / reinitializer.** One-shot `fn initializer` (and OZ component initializers) set owner/roles. Without a persistent "already initialized" flag, an attacker front-runs deployment or re-runs it after an upgrade. A caller-only condition is not a guard.
- **Component ownership.** A contract can embed `OwnableComponent` and a second component whose admin functions are embedded but do not consult `ownable`. Trace which component owns each entry point.
- **Ownable pitfalls.** Owner never initialized defaults to `Zeroable::zero()`; `transfer_ownership` to zero bricks admin; `renounce_ownership` left reachable; an inherited `owner()` reading the wrong base. Confirm exactly one owner exists.
- **Self-call / dispatcher trust.** A guard that only compares against a trusted contract address is bypassable if any caller can make that trusted contract call the guarded function.
- **Constructor vs initializer.** State set in the constructor is fixed; state set by an initializer is re-callable. Mixing them (a constructor that sets an owner the initializer can overwrite) is a takeover.
- **Pause / emergency functions.** `pause`, `emergency_withdraw`, config setters — check each has the intended guard, not just the "main" functions.

## Attack plan

1. Build the map: entry point → guard (`assert_only_owner` / role check / inline compare) → state written.
2. For every privileged entry, ask whether an unprivileged caller can reach the same state via a component method, an `#[abi(embed_v0)]` method, or a helper in the external impl.
3. Inspect `upgrade`: is it owner-gated, and is `new_class_hash` constrained?
4. Probe initializers: front-run, re-call, and call after `upgrade`.
5. Check whether `owner`/roles default to zero and whether the zero address passes a guard.
6. Escalate from any foothold toward owner, funds, or `replace_class_syscall`.

## Proof

Use `snforge` with `starknet::testing::{set_caller_address, set_contract_address}`. For a missing guard, call the privileged entry as an attacker and show the effect. For an unguarded upgrade, replace the class and then call attacker code through the proxy address. For an initializer, call it twice (or front-run) and show the takeover. A missing modifier alone is a lead; a working trace is the finding.

## Fix

Gate every privileged function with `assert_only_owner()` or a role check and use `get_caller_address()`. Keep unprivileged helpers out of `#[external(v0)]`. Only `#[abi(embed_v0)]` components whose methods are internally guarded. Guard `upgrade` with owner + class validation and document that storage layout is the caller's responsibility. Make initializers idempotence-checked and set the owner before any external call.

## Variants and adjacent bugs

- **Unguarded `upgrade`** — public, or missing `assert_only_owner`.
- **Missing guard on a sibling writer** — one setter guarded, another not.
- **Re-runnable initializer** — no persistent initialized flag.
- **Embedded component admin** — `#[abi(embed_v0)]` without an internal owner check.
- **Zero-address owner** — an uninitialized `owner` compared with `==`.

## Do not flag

- Admin-only entry points performing admin actions by design.
- `#[external(v0)]` functions that call `assert_only_owner()` on every path.
- Deploy-then-initialize sequences that are atomic (constructor or factory).

## Leads vs findings

- A missing `assert_only_owner()` is a **lead**; taking a privileged effect is the finding.
- Show the attacker call, the bypassed guard, and the privileged state change.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/cairo` — component and visibility model.
- `tooling/cairo-scarb` — build and test commands.
- `vulnerabilities/upgradeability-proxy` — storage layout and upgrade risks.
