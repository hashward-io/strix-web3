---
name: insecure-defaults
description: Hunt insecure default configuration — zero admin, uninitialized state, unbounded approvals, permissive fallbacks, debug flags, and unset-but-assumed config
---

# Insecure Defaults

Every default that ships is a decision an attacker can exploit. A field left at zero, an owner never set, an approval never bounded, a fallback that accepts anything, a config the code assumes but never validates — deployment-time bugs live here. Safe code and safe configuration are different claims; this skill audits the configuration.

## The default catalogue

**Zero / empty authority.** An admin/owner/guardian variable defaults to `address(0)` (EVM), a default pubkey, or an unset `AdminCap`. If a privileged function checks `msg.sender == owner` and `owner` is still zero, the call may pass from the zero identity, or the function bricks forever. Look for an `initialize` that must be called and can be front-run.

- EVM: proxy whose implementation is set in the constructor but whose `__Ownable_init` never runs; uninitialized `owner`.
- Solana: `authority` in an account defaults to `Pubkey::default()`; missing `has_one = authority`.
- Move: no `AdminCap` created, or `init` mints the capability to a predictable address.
- CosmWasm: `admin` set to empty/`None` in `InstantiateMsg`, so `MigrateMsg` is uncallable or world-callable.
- Cairo: `owner` storage defaults to `0`; a re-entrant `initialize` resets it.

**Default owner / first-caller-wins.** `initialize()` callable by anyone once, with no deployer gate, lets an attacker become owner before the team does. This is the uninitialized-proxy race.

**Unbounded approvals / allowances.** `approve(spender, type(uint256).max)` to an arbitrary spender, an infinite allowance to a router, or a blanket `setApprovalForAll`. Each is a standing grant inherited by an attacker if the spender is compromised or attacker-controlled.

**Missing or partial initialization.** A field assumed initialized by one function but not by another; a counter left at `0` where `0` is also a valid sentinel; a rewards index initialized to `0` with existing stakers.

**Permissive fallback / catch-all.** An EVM `fallback()`/`receive()` that accepts value and forwards `msg.data` to a caller-chosen target; a Solana handler that ignores leftover accounts; a Move `public entry` that accepts any object. A broad dispatcher turns every call into an authenticated action.

**Debug flags left on.** A disabled `require`, a `paused`/`frozen` default, a commented-out `onlyOwner`, a `testMode`/`skipChecks` boolean, a mock oracle wired in, a hardcoded dev signer, or `assert` swapped for `require`.

**Default mints / fees / rates.** A constructor that mints the entire supply to `msg.sender`; an initial `feeBps = 0` that a setter can raise unbounded; a default fee of `100%`. A default of 0 often means "fails open".

**Unset-but-assumed config.** A value the code reads but nothing writes: `maxLeverage == 0` used as a divisor, an oracle address never set, a whitelist mapping left empty (accept-all) when the check is `if (allowed[x]) revert`. An empty mapping is a fail-open allowlist, not a fail-closed one.

## How to find them

1. Enumerate every state variable and storage slot with its initial value (constructor / `init` / `#[ink(constructor)]` / `initializer`).
2. For each, ask who can write it after deployment, and whether the unwritten value is safe or exploitable.
3. Diff every config value against its use site: a value read but never written is a lead.
4. Read the deployment scripts (`Deploy.s.sol`, `migrate`, `#[init]`) for initialization order and any step an attacker can front-run.
5. Re-read the first `if`/`require` in every privileged function with the field at its default.

## Attack plan

- Find a privileged function whose guard reads a default (zero) member → unauthorized access or a brick.
- Find a one-shot initializer with no caller restriction → front-run to own the contract.
- Find a fail-open check (empty allowlist, zero fee, reversed blocklist) → bypass policy with a default identity.

## Proof

A test that calls the privileged function with the field at its default value and shows the unauthorized effect (ownership taken, funds moved, function bricked). Name the default value and the missing write.

## Fix

Reject zero/empty authority at deployment (`require(owner != address(0))`); gate initialization to the deployer or use an atomic initializer/factory; default allowlists to deny; bound approvals; remove debug hooks; validate every config value at set-time and at use-time.

## How to apply

1. List all state, its default value, and the function that writes it.
2. Flag every read-before-write and every fail-open default (empty mapping, zero fee, zero authority).
3. Flag every one-shot initializer without a caller gate.
4. Escalate each to the strongest impact (takeover, drain, brick) with concrete default values.
5. Record as a FINDING with a PoC, or a LEAD with unproven reachability; feed missing-init invariants to `analysis/invariant-discovery` and stress them with `analysis/counterevidence`.
