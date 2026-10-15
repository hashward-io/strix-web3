---
name: bridges-messaging
description: Bridges and cross-chain messaging — replay, message validation, finality, relay trust, and mint/burn accounting
---

# Bridges and Cross-Chain Messaging

A bridge holds value on one chain and mints/releases it on another based on a message. Every trust assumption in that message path is an attack surface.

## Where to look

- **Replay.** A message without a unique nonce/destination/chainId replayable on the same or another chain (a fork of the source chain reuses message IDs). Each message must be consumed exactly once (an `executed` mapping keyed by a hash that includes `chainId` + `nonce` + sender + payload).
- **Message validation.** Who can relay, and what do they attest? A single relayer that is a hot key; a signature quorum with a threshold that can be met by the attacker; a light-client/proof verification with a weak or forgeable proof; a `verify` that does not bind the payload.
- **Finality.** Acting on a source-chain event before it is final; a reorg that double-spends the bridge. Check the confirmations/finality delay.
- **Source validation.** The receiving side must check the message actually came from the trusted source contract/chain; a missing `msg.sender == endpoint` check.
- **Mint/burn / lock/**release accounting. Locked on source must equal minted on destination; a mint with no lock, a release with no burn, a double-release, a wrapped-token admin that can mint.
- **Rate limits / caps.** A per-tx / per-epoch cap; a cap that is bypassable by splitting, or one that is missing entirely so a single compromised relayer drains the bridge.
- **Token/NFT bridging.** A message that mints the wrong token; an NFT collection whose ids collide; a fee that is not accounted.
- **Governance/admin.** An upgradeable bridge with a single-admin upgrade (see `vulnerabilities/upgradeability-proxy`); an `unpause`/`emergencyWithdraw` that can be abused.
- **Gas/relayer griefing.** A message that always reverts on the destination (blocking the queue); gas limits that make relay profitless.

## Attack plan

1. Trace a message end-to-end: source event → relayer → destination `execute`.
2. For each field the destination trusts, ask whether it is validated and unique.
3. Check replay: try the same message twice, then on a fork/another chain.
4. Check finality and source authentication.
5. Check the mint/burn/lock/release accounting and any rate limit.

## Proof

For replay, show a message executed twice with the same effect. For a validation gap, show a forged message accepted. For conservatism, show minted > locked.

## Fix

Consume each message once (hash with chainId+nonce); authenticate the source endpoint; verify a real proof or a robust quorum; enforce finality delays; keep lock/mint accounting exact; add rate limits; timelock admin.
