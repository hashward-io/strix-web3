---
name: intents-and-solvers
description: Intent and solver systems — order validity, nonce/replay, EIP-712/Permit2/ERC-1271 signatures, filler settlement, auction fairness, partial fills, and escrow refunds
---

# Intents and Solvers

An intent declares a desired end state; a solver fills it. A user signs an order, a settlement contract
escrows and pays, and a third party races to satisfy it. Every gap between the signed order, the on-chain
fill, and the settlement payment is exploitable.

## Domains

- **Order validity.**
  - The signed struct (`maker`, `receiver`, `input`, `output`, `deadline`, `nonce`, `partiallyFillable`, fees) defines validity.
  - Check that `fill`/`execute` re-derives the same hash and enforces every field: limit price, deadline, and remaining amount.
  - A Dutch-auction decay that can be raced to the worst price, or an order that stays valid after cancellation.
- **Signature schemes.**
  - EIP-712 domains must bind `chainId` and `verifyingContract`.
  - Permit2 adds `permit`/`permitTransferFrom`/`permitWitnessTransferFrom` with a witness for the intent — a classic replay surface.
  - Smart-contract makers validate through ERC-1271: check the `_hash` is restricted and replay is impossible.
  - Include `ecrecover` malleability, batch signatures, and multi-signature aggregate orders (`vulnerabilities/signature-replay`).
- **Nonce / replay.** One-shot nonces, bitmap nonces for partial fills, a `filled` mapping, and `cancel`. A nonce not consumed on use, a cancel that does not invalidate, or an order replayable on another chain/domain is a replay. Cross-chain intents replay across the source/destination legs (see `protocols/bridges-messaging`).
- **Solver / filler trust and settlement.**
  - Who can call `fill`? Does settlement hold user escrow or pull via Permit2?
  - Check `msg.sender` checks, arbitrary external calls from the settlement contract, solver bonds, and a filler that receives the output without delivering the input.
- **MEV and auction fairness.**
  - Dutch (first-price decay), batch, and sealed-bid auctions; solver competition and priority-gas bidding.
  - Look at bid leakage, an auctioneer that can censor or reorder, a uniform-price rule that overpays, and a solver that backruns the price decay (`vulnerabilities/mev-frontrunning`, `hacking_agents/economic-security`).
- **Cross-chain intents.** A destination fill authorized before the source is proven, relayer trust, message authentication, and order-hash binding across chains (see `protocols/bridges-messaging`).
- **Partial fills.** Remaining amount, rounding, dust, multiple fillers summing past the total, an overfill, or locked funds when `partiallyFillable` is mis-set.
- **Escrow / refund handling.** Release to maker/solver on expiry, native-token handling, reentrancy on refund (`vulnerabilities/reentrancy`), and a griefing expiry that traps funds or blocks a legitimate fill.
- **Fee and recipient handling.** A fee taken from the wrong side, a `recipient`/`feeRecipient` that is attacker-set, or a refund sent to the filler instead of the maker.
- **Non-EVM analogue.** Solana intents arise from signed `transferChecked`/`approve` delegations and off-chain order books; check `secp256k1`/`ed25519` instruction introspection, durable nonces, and PDA-mediated settlement (`ecosystems/solana`).

## Where to look

- Order struct, `hashOrder`, `getOrderHash`, `_verifySignature`, `isValidOrder`, `fill`, `execute`, `matchOrders`, `fulfill`.
- Permit2 `permitTransferFrom`, `permitWitnessTransferFrom`, `nonceBitmap`, `allowance`, and the witness type string.
- Nonce state: `filled`, `cancelled`, `nonces`, `nonceBitmap`, `incrementNonce`, `cancel`.
- Settlement: escrow/deposit balances, `msg.sender` gates, external calls, fee split, `receiver`, and native/ERC-20 payout paths.
- Auction state: current price/decay curve, `block.timestamp`, bid lists, solver registry and bonds.
- Order fill reads: `remaining`, `filled`, `available`, and any view the UI trusts before signing.
- Cross-chain: `srcChainId`/`dstChainId`, message authentication, and order-ID derivation.
- Fee accounting: `feeBps`, `feeRecipient`, and the protocol-fee vs solver-fee split.

## Attack plan

1. Recompute the order hash from the struct; drop each field to find one the fill does not bind or enforce.
2. Replay: fill twice with one nonce, fill after cancel, fill on another chain/contract, or over-fill a partial order.
3. Forge a settlement path: call `fill` as an untrusted filler, redirect `receiver`, or make the settlement call an attacker target.
4. Race the auction: backrun the decay, leak a sealed bid, or censor a solver.
5. For cross-chain, show a destination fill before source proof or a replayable order id.
6. Attack refunds: re-enter on expiry release or grief the escrow so a fill is impossible.

## Proof

A Foundry PoC: a replayed or over-filled order, an unauthorized filler that extracts value, a partial-fill
overrun, or an auction/escrow manipulation with concrete amounts. Cross-chain proofs need both legs or a
mock. No reachable trace or economics means a **lead** (`analysis/finding-contract`).

## Fix / Mitigations

Hash and enforce every order field, including `deadline` and limit price; bind signatures to
`chainId`+`verifyingContract` and consume per-maker nonces on fill and cancel; validate ERC-1271 signers
strictly; restrict who may settle and never make arbitrary external calls from settlement; escrow via
Permit2 or internal balances with checks-effects-interactions on refunds; enforce partial-fill accounting
with rounding in the protocol's favor; use commit-reveal or a batch/uniform-price rule and bond solvers for
auction fairness; authenticate cross-chain messages before releasing funds (`protocols/governance`,
`protocols/bridges-messaging`).
