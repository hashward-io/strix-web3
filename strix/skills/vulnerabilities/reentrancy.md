---
name: reentrancy
description: Reentrancy — single-function, cross-function, cross-contract, read-only, and callback reentrancy in Solidity
---

# Reentrancy

An external call hands control to code you do not control. If state is inconsistent when control leaves, the callee (or a callback it triggers) can re-enter and exploit it.

## Variants

- **Single-function** — state updated after an external call (`transfer` then subtract balance). Classic; the `nonReentrant` guard usually covers it.
- **Cross-function** — two functions share state; function A makes the external call, the reentrancy re-enters function B. `nonReentrant` on A alone does **not** help if B is unguarded. Check every function that reads state A leaves inconsistent.
- **Cross-contract** — the re-entered function lives in another contract of the same protocol (vault → strategy → vault). `nonReentrant` is per-contract; a shared lock or checks-effects-interactions across the boundary is required.
- **Read-only reentrancy** — you don't need to write state. If a view (e.g. `get_virtual_price`, `totalAssets`, a price getter) reports an inconsistent value mid-callback, any *other* protocol that reads it during the callback is exploitable. This is the highest-value variant and the one `nonReentrant` never fixes.
- **Callback / hook reentrancy** — ERC-777 `tokensReceived`, ERC-1155 `onERC1155Received`, ERC-721 `onERC721Received`, flash-loan callbacks, `onFlashLoan`, Uniswap `uniswapV3SwapCallback`, `onERC3156FlashLoan`. Any of these lets an attacker re-enter while balances are mid-update.

## Where to look

- Every external call: `.call{...}`, `.transfer`, `.send`, `safeTransfer*`, native sends, and any `IERC20(token).transfer` where the token is attacker-chosen.
- State writes that happen **after** the external call (effects-after-interactions).
- Guards: is `nonReentrant` present, and does it cover *all* functions sharing the touched state — including view functions that a peer protocol reads?

## Proof

Concrete trace: the entry function, the external call, the re-entered function, the inconsistent value observed, and the profit. A Foundry PoC with a malicious token/callback contract is the gold standard. For read-only reentrancy, show the peer consumer reading the stale view.

## Fix

Checks-effects-interactions; `nonReentrant` on every state-sharing entry; a reentrancy guard on view functions that peers consume; or pull-payment patterns. State the residual risk if a token or callback is inherently reentrant.
