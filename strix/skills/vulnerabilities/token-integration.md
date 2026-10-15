---
name: token-integration
description: Arbitrary-token integration — fee-on-transfer, rebasing, blacklisting, ERC-777/1155 hooks, decimals, and non-standard ERC-20 behavior
---

# Token Integration

If the protocol accepts arbitrary tokens, every non-standard behavior is a potential bug. The protocol's math assumed a plain ERC-20.

## Non-standard behaviors to test

- **Fee-on-transfer.** `transfer(recipient, amount)` delivers `amount - fee`. If the code credits `amount` (to a balance, a pool reserve, or a share), accounting drifts. Always measure `received = balanceAfter - balanceBefore`.
- **Rebasing / elastic supply.** A token whose `balanceOf` changes without a transfer (stETH, AMPL) breaks any cached balance or any invariant `sum(balances) == balanceOf(contract)`.
- **Blacklisting / pausing.** A transfer that reverts for a specific address makes a shared function revert for everyone (DoS of `withdraw`/`liquidate` loop) or locks funds.
- **ERC-777 / ERC-1155 / ERC-721 hooks.** `tokensReceived`, `onERC1155Received`, `onERC721Received` re-enter the sender mid-update — reentrancy through a "trusted" token.
- **Void-return and false-return.** USDT returns nothing; some tokens return `false` instead of reverting (see `vulnerabilities/unchecked-returns`).
- **Multiple entry points.** Two addresses for the same token (proxy + implementation, or a bridged duplicate) — a check `token == expected` fails, or a balance sums both.
- **Decimals.** 0-decimal, 6-decimal, and 24-decimal tokens; a hard-coded `1e18`; a `decimals()` call that reverts on a non-standard token.
- **`approve` race / infinite approval.** Setting a new allowance while an old one is unspent; relying on `approve` returning `true`.
- **Transfer to `address(this)`.** A user can send tokens directly to the contract, changing any balance-derived accounting (see donation attacks).
- **Malicious token callbacks.** A token whose `transfer` calls back into the protocol.

## Attack plan

1. List every token the protocol touches and whether it enforces a token allowlist or accepts arbitrary tokens.
2. For each integration, ask which non-standard behavior breaks it, and trace the accounting consequence.
3. For swap/liquidity math, compute the shortfall with a fee-on-transfer token.
4. For any `balanceOf(contract)`-based accounting, test a direct donation.

## Proof

A Foundry PoC with a mock fee-on-transfer, rebasing, or hook token that breaks an invariant or yields a profit. Name the assumption (e.g. "received == amount") and show the divergence.

## Fix

Measure received amounts; use `SafeERC20`; forbid or explicitly handle fee-on-transfer/rebasing tokens; make accounting internal rather than balance-based; protect against token-callback reentrancy; normalize decimals via the token's own `decimals()` with a safe fallback.
