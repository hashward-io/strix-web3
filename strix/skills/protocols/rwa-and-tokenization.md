---
name: rwa-and-tokenization
description: RWA tokenization — permissioned transfers, KYC allowlists, compliance hooks, NAV/oracle pricing, redemption queues, admin powers, and cross-chain representations
---

# RWA and Tokenization

Real-world-asset tokens wrap an off-chain legal claim in an on-chain bearer instrument. The value lives
off-chain, but transfer, pricing, and redemption rules live in contracts that a privileged operator
usually controls. Read the token as a compliance state machine with an admin back door.

## Domains

- **Permissioned / allowlisted transfers.**
  - ERC-3643 (T-REX), ERC-1400/ERC-1404, and bespoke tokens gate `transfer`/`transferFrom` on an identity registry.
  - Every value-moving path must consult the gate: `transfer`, `transferFrom`, `mint`, `burn`, `forcedTransfer`, and any ERC-20 wrapper or conduit.
- **KYC / transfer restrictions.**
  - The identity registry maps wallets to `onchainID` contracts whose claims (KYC, country, investor class) are issued by trusted claim issuers.
  - A missing, expired, or revoked claim; a forfeited country restriction; or a lockup that is not enforced are all bypasses.
  - Check claim-topic validation and issuer trust, not just "is registered".
- **Compliance hooks.** T-REX `Compliance.canTransfer`/`transferred` and modular compliance rules. A hook skipped on mint/burn, on a `setCompliance` swap, or in a peer that moves balances directly is the classic gap.
- **NAV / oracle pricing.**
  - Net asset value may be admin-set or fed by an oracle; `mint`/`redeem` at a stale NAV is free money.
  - Check staleness/heartbeat, market-hours and weekend gaps, the decimals of the NAV unit, and rounding.
  - A NAV update can be front-run or sandwiched (`vulnerabilities/oracle-manipulation`, `vulnerabilities/mev-frontrunning`).
  - An optimistic NAV oracle adds a dispute window and bond surface.
- **Redemption / withdrawal queues.**
  - FIFO or epoch queues with `requestRedeem`/`cancelRedeem`/`claim`.
  - Look at liquidity mismatch (illiquid assets, one-asset liquidation), queue jumping, partial fills, and cancellation that returns a worse NAV.
  - A `claim` whose outcome depends on the caller, or a snapshot taken before a deposit settles.
- **Legal / admin powers.** Pauser, freezer/blacklister, `forcedTransfer`/seize, `mint`/`burn` while paused, `upgrade`, `setCompliance`, `setIdentityRegistry`, NAV setter, and `transferOwnership`. Each is a centralization trust boundary; ask whether a non-admin can reach a privileged effect.
- **Cross-chain RWA.** Bridged/wrapped representations (see `protocols/bridges-messaging`). The allowlist, freeze, and NAV may diverge per chain; a burn on one leg and a mint on the other can drift, and a set of per-chain minters can double-mint.
- **Lockups and soulbound rules.** A holding period enforced by timestamps, or a transfer lock a privileged agent can clear; a `validUntil` never checked against `block.timestamp`.
- **Decimals and unit mixing.** NAV priced per whole unit while the token has non-18 decimals; a `1e18` constant applied to a 6-decimal underlying.

## Where to look

- Token `_beforeTokenTransfer`/`_update`, `transfer`, `transferFrom`, `mint`, `burn`, `forcedTransfer`, `freeze`/`unfreeze`, `pause`/`unpause`.
- `IdentityRegistry.isVerified`, `Identity.addClaim`/`removeClaim`, `ClaimIssuer.isClaimValid`, claim topics, `onchainID`.
- `Compliance.canTransfer`, `transferred`, `bindToken`, and the modular-rule registry.
- `requestRedeem`, `cancelRedeem`, `claim`, `deposit`, `withdraw`; epoch/snapshot state and `pending`/`fulfilled` accounting.
- NAV getter, oracle adapter, `setNav`, heartbeat/staleness constants, `pricePerShare`.
- Access-control roles: `TransferAgent`/`Agent`/operator permissions, proxy admin, and initializers.
- Bridged token `mint`/`burn` callers and the cross-chain message authentication they rely on.
- `paused()`/`frozen(address)`/`isBlacklisted` and their modifiers on every entry point.
- Snapshot/epoch state used to compute redemption NAV (`epoch`, `redeemEpoch`, `snapshotSupply`).

## Attack plan

1. Enumerate every way a balance can move (including mint/burn/forced transfer) and confirm each runs the allowlist and compliance checks.
2. Break a claim: use an expired, wrong-country, or wrong-topic claim, or a revoked identity, and show the transfer still passes.
3. Attack pricing: mint or redeem against a stale/manipulable NAV, or sandwich a NAV update; check decimals and rounding direction (`vulnerabilities/precision-rounding`).
4. Attack the redemption queue: jump the queue, cancel into a better NAV, or grief a `claim`.
5. Walk the admin graph: can any non-admin reach pause, freeze, seize, upgrade, or NAV-set?
6. For cross-chain, show an allowlist/freeze/NAV divergence or a mint without a matching burn.

## Proof

A Foundry PoC on a fork or mock: a restricted transfer that succeeds (identity/claim bypass), a
mint/redeem that extracts value at a stale NAV, or a queue manipulation with concrete amounts. For an
admin-power issue, show the reachable privileged effect and who can trigger it. Economic findings need
numbers, or they are leads (`hacking_agents/economic-security`).

## Fix / Mitigations

Route every balance mutation through one checked `_update`; validate claim topics, issuer, expiry, and
jurisdiction on every transfer; run compliance hooks on mint/burn/forced transfer and on module changes;
use a staleness-checked, manipulation-resistant NAV and round in the protocol's favor; design redemption
queues with explicit NAV and partial-fill semantics; timelock and role-gate admin powers and document them
as trust boundaries; reconcile per-chain supply and allowlists across the bridge (`protocols/governance`).
