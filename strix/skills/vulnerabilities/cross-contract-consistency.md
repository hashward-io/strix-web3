---
name: cross-contract-consistency
description: Cross-contract and cross-chain consistency — stale caches, assumption drift, callback ordering, and unsynchronized state
---

# Cross-Contract Consistency

When two contracts (or two chains) each hold part of a truth, the truth can diverge. The bug is in the seam, not in either contract.

## Where to look

- **Stale caches.** Contract A caches a value from contract B (a price, a balance, a debt) and does not refresh it before use. B changes; A's decision is made on the old value.
- **Assumption drift.** A caller assumes a callee's property (reserves only increase, `totalSupply` only minted, a getter is monotonic) that the callee can violate through a permissionless function.
- **Unsynchronized mirrors.** Two contracts track the same "truth" (an LP's debt, a user's collateral) and one updates without notifying the other. Cross-chain bridges with a local mirror are the classic case (see `protocols/bridges-messaging`).
- **Callback ordering.** A callback (flash loan, hook, `onX`) fires between two writes of the same logical operation, leaving a peer contract reading a half-updated state (read-only reentrancy's cousin).
- **Reentrancy via a peer.** A → B → callback → A, where A's state is mid-update.
- **Oracle-of-oracle.** A value derived from a peer protocol's derived value, where the peer's value is manipulable.
- **Cross-chain replay / finality.** A message valid on one chain replayed on another, or acted on before finalized (see bridges/messaging).
- **Initialization order.** Contract A's constructor/initializer assumes B is already deployed and configured; a deploy script that orders them wrong (deploy scripts are in scope).
- **Upgrade desync.** A proxy upgraded but a peer that cached its implementation address not updated.

## Attack plan

1. Map the contract graph; for every edge, list what the caller assumes about the callee.
2. For each assumption, find a callee function that violates it permissionlessly.
3. For each multi-write logical operation that makes an external call in the middle, find a peer that reads the intermediate state.
4. For cross-chain, check replay and finality assumptions.

## Proof

Show the sequence: caller reads stale/half-updated value from the callee → decision → impact. Name the assumption and the callee function that breaks it.

## Fix

Refresh cached values before use or read live; make assumptions explicit and enforce them (re-check on the callee side); order writes before external calls (CEI); use reentrancy guards on the readers too; for cross-chain, bind messages with nonces and chain IDs and wait for finality.
