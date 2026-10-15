---
name: unchecked-returns
description: Unchecked external call results — low-level call success, ERC20 transfer/approve return values, and silent failures
---

# Unchecked Returns and Silent Failures

A call can fail without reverting. If the code ignores that, it proceeds as if it succeeded.

## Where to look

- **Low-level `.call` result ignored.** `target.call(data);` without checking the returned `bool` (and without `require`/`if (!success) revert`). The state transitions as if the call succeeded.
- **`.send` return ignored.** `payable(x).send(v);` returns `false` on failure; ignoring it loses the payment silently. (`.transfer` reverts on failure but is capped at 2300 gas — a DoS vector for contracts with a `receive`.)
- **ERC-20 return values.** `transfer`/`transferFrom`/`approve` return `bool`; some tokens return `false` instead of reverting, some return nothing (USDT), some return `true` always. A raw `token.transfer(...)` that ignores the result silently fails on a `false`-returning token. Use `SafeERC20`.
- **Non-standard tokens.** Fee-on-transfer: the recipient receives less than `amount`, but the code credits `amount`. Rebasing: balances change without a transfer. `approve`-race: setting a new allowance before the old is spent.
- **`delegatecall` result ignored.** Same as `.call`, but the context is the proxy's.
- **`permit`/`try` patterns.** A `try/catch` that swallows the failure and continues with a default.
- **Batched calls.** A multicall where one failed call is silently skipped and the rest proceed against inconsistent state.
- **Code-existence checks.** A `.call` to a non-contract address succeeds with empty return data; without an `extcodesize` check, a token that does not exist is treated as returning success.

## Attack plan

1. Enumerate every external call and whether its success/return value is used.
2. For each ERC-20 interaction, check whether it uses `SafeERC20` or checks the boolean, and whether it assumes a standard token.
3. For each low-level call, check the `success` boolean and any return-data decode.
4. Look for fee-on-transfer / rebasing / void-return tokens that break the credited amount.

## Proof

Show the failing call and the resulting inconsistent state, or the fee-on-transfer shortfall credited as full. A Foundry PoC with a mock `false`-returning or fee-on-transfer token is ideal.

## Fix

Use `SafeERC20` for all token calls; check every low-level call's success; measure received amount (`balanceAfter - balanceBefore`) rather than trusting the input; add `extcodesize` checks for expected contracts; use `try/catch` deliberately, not to swallow.
