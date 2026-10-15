---
name: weird-erc20
description: Token-quirk checklist distilled from d-xo/weird-erc20 — non-standard ERC-20 behaviors that break integrations, with the defensive pattern for each
---

# Weird ERC-20 Checklist

The ERC-20 "spec" is loose enough that many real tokens violate it, and protocols that assume a plain token lose funds. This checklist distills the d-xo/weird-erc20 catalog of real, weird tokens into integration checks. The default defenses: keep a contract-level **allowlist of known-good tokens**, and interact with tokens through dedicated **wrapper/adapter contracts** at the system edge so the core can assume known semantics. When permissionlessness forbids an allowlist, be highly defensive and remember an off-chain UI allowlist still protects unsophisticated users.

## Return-value and failure quirks

- [ ] **Missing return values** — `transfer`/`transferFrom`/`approve` return no `bool` (USDT, BNB, OMG). Prevent: use a `SafeERC20`-style abstraction that tolerates no return value.
- [ ] **Returns `false` instead of reverting** — declares `bool` but returns `false` even on success (Tether Gold). Prevent: never trust the return value alone; reconcile via `balanceOf`.
- [ ] **No revert on failure** — returns `false` rather than reverting (ZRX, EURS). Prevent: always wrap in `require` or `SafeERC20`.
- [ ] **Revert on zero-value transfer** — reverts for `amount == 0` (LEND). Prevent: skip zero-value transfers.
- [ ] **Revert on transfer to zero address** — breaks burn-by-transfer (OpenZeppelin). Prevent: use the token's burn, not `transfer(address(0))`.
- [ ] **Revert on zero-value approval** — reverts for `approve(spender, 0)` (BNB); also reverts on `approve(address(0), amt)`. Prevent: handle both cases.

## Balance and supply quirks

- [ ] **Fee-on-transfer** — the recipient receives less than `amount` (STA, PAXG; was used to drain Balancer pools). Prevent: measure `balanceAfter - balanceBefore` and credit the received amount.
- [ ] **Rebasing / balance change outside transfers** — `balanceOf` changes without a transfer (Ampleforth); cached balances go stale. Prevent: don't cache balances; or special-case the rebase.
- [ ] **Airdrops** — out-of-band balance increases (Compound-style). Prevent: reconcile rather than assume transfers are the only balance change.
- [ ] **Flash-mintable** — total supply can spike within a tx (DAI). Prevent: don't assume `totalSupply` is bounded.
- [ ] **Transfer of less than amount** — a `type(uint256).max` special case that transfers only the balance (cUSDCv3). Prevent: credit what was actually transferred.
- [ ] **`transferFrom` with `src == msg.sender`** — some tokens skip the allowance decrement, giving `transferFrom` `transfer` semantics (DSToken). Prevent: don't rely on allowance side effects.

## Approval quirks

- [ ] **Approval race protection** — refuses `approve(M>0)` when an existing `N>0` allowance is set (USDT, KNC). Prevent: set to 0 first, then set the new value.
- [ ] **Large approvals / transfers** — reverts above `uint96` (UNI, COMP), with a `type(uint256).max` special case. Prevent: cap approvals; the stored allowance may not equal the input.
- [ ] **Unusual `permit`** — a `permit()` that does not follow EIP-2612 and may not revert on failure (DAI, RAI, and others). Prevent: use Permit2 or verify the implementation.

## Identity and metadata quirks

- [ ] **Multiple token addresses** — a proxied/upgraded token has more than one address; a single-address check lets `rescueFunds` drain pool tokens. Prevent: map all known representations.
- [ ] **Proxy / upgradeable token** — logic can change at any time (USDC, USDT). Prevent: detect an upgrade and freeze or re-validate semantics.
- [ ] **Native-currency ERC-20** — chains expose a native token as ERC-20 (Celo CELO, Polygon POL, zkSync ETH). Prevent: avoid double-counting native + wrapped balances.
- [ ] **Non-string metadata** — `name`/`symbol` encoded as `bytes32` (MKR). Prevent: decode defensively.
- [ ] **Code injection via token name** — malicious `name` carrying frontend script (EtherDelta exploit). Prevent: sanitize any token metadata rendered in a UI.

## Decimals and administration

- [ ] **Low decimals** — 6 (USDC) or 2 (Gemini USD) → larger precision loss. Prevent: normalize via `decimals()`.
- [ ] **High decimals** — >18 (YAM-V2, 24) → overflow/liveness. Prevent: use wide types; check scaling.
- [ ] **Blocklists** — admin can forbid an address (USDC, USDT) and trap protocol/LP funds. Prevent: handle blocked-address reverts; assess admin risk.
- [ ] **Pausable tokens** — admin can pause (BNB, ZIL), freezing the protocol's flows. Prevent: pause-aware logic and a fallback path.

## Reentrancy

- [ ] **Reentrant transfer** — a token with a hook calls back on `transfer` (ERC-777; imBTC/lendf.me drains). Prevent: reentrancy guards on every token-touching path (`vulnerabilities/reentrancy`).

## Metadata and interface edge cases

- [ ] **Reverting or missing `decimals()`** — some tokens revert or omit it. Prevent: a safe fallback and an explicit default.
- [ ] **`permit` replay across chains** — an EIP-2612 domain that omits `chainid`. Prevent: full EIP-712 domain.
- [ ] **`approve`-race front-run** — a spender front-runs an allowance change. Prevent: set allowance to zero first, or use `increaseAllowance`.
- [ ] **Unbounded `totalSupply`** — mintable/flash-mintable tokens break bounded-supply assumptions.

## Sources

- d-xo/weird-erc20: https://github.com/d-xo/weird-erc20
- Trail of Bits token integration checklist and ConsenSys Diligence token checklist (linked from the repo).
- Companion skills: `vulnerabilities/token-integration`, `vulnerabilities/unchecked-returns`.
