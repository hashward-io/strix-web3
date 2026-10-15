---
name: access-control
description: Access control — unprotected functions, missing/incorrect modifiers, broken initialization, privilege escalation, role confusion
---

# Access Control

Map the complete permission surface, then attack every gap.

## Where to look

- **Unprotected state-changing functions** — an `external`/`public` function that writes privileged state with no modifier and no inline `msg.sender` check.
- **Inconsistent guards on shared state** — for every storage variable written by 2+ functions, find the one with the weakest guard. If A is `onlyOwner` but B writes the same variable unguarded, use B. Check inherited helpers and `internal` functions reachable from differently-guarded `external` ones.
- **Initialization** — an `initialize()` that lacks an `initializer` modifier, is callable by anyone, or can be front-run; an implementation contract left uninitialized; a proxy whose initializer was never called.
- **Role confusion** — `onlyRole(A)` where the action needs role B; a role that can grant itself other roles; `DEFAULT_ADMIN_ROLE` granting itself arbitrary roles; a `renounceRole`/`grantRole` asymmetry.
- **Missing check on the "sensible" path** — `setFee` guarded, `emergencyWithdraw` not; `mint` guarded, `burn` not.
- **`tx.origin`** used for authorization (phishing-vulnerable).
- **Delegatecall target control** — a user-influenced or storage-set target executed with `delegatecall`.
- **Signature-less admin paths** — a function intended to be called only by a contract/keeper that any caller can reach.

## Attack plan

1. Build the map: role → functions → state.
2. For each privileged action, ask "can I reach that state transition as an unprivileged actor, directly or via an internal helper, an inherited override, or a differently-guarded sibling?"
3. For each one-shot init, ask "can I front-run or re-enter it?"
4. Escalate: from any unprivileged foothold, can I reach `DEFAULT_ADMIN_ROLE`, funds, or an upgrade?

## Proof

Name the actor, the function, the missing/incorrect guard, and the privileged effect achieved. Show a trace: attacker call → unguarded path → privileged state change.

## Do not flag

Admin-only functions doing admin things by design. `nonReentrant` is not access control. `initializer`/`reinitializer` one-time functions are tracked separately, not flagged for existing.
