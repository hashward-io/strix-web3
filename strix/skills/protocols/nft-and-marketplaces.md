---
name: nft-and-marketplaces
description: NFT and marketplace review — ERC-721/1155 receiver reentrancy, lazy signature mints and replay, ERC-2981 royalties, escrow settlement, and batch-mint DoS
---

# NFT and Marketplaces

NFTs add a transfer hook the receiver controls and an off-chain order book the marketplace trusts. Both
turn a simple token into a reentrancy and signature surface, and a settlement engine into an escrow.

## Domains

- **ERC-721/1155 receiver reentrancy.**
  - `safeTransferFrom` calls `onERC721Received` / `onERC1155Received` / `onERC1155BatchReceived` on the recipient.
  - Minting, settling, or refunding to an attacker contract re-enters before state is final.
  - Check read-only reentrancy through `ownerOf`/`balanceOf`/`totalSupply` used by peer contracts.
- **Lazy / off-chain signature mints and replay.**
  - EIP-712 vouchers (Seaport-style orders, mint-pass signatures). The signed struct must bind `chainId`, `verifyingContract`, the order/collection, price, nonce, and deadline.
  - A missing `counter`/nonce, an unused `deadline`, or a domain shared with another contract enables replay (`vulnerabilities/signature-replay`).
  - Include `ecrecover` malleability and ERC-1271 for smart-contract signers.
- **Cancellation and partial fill.** `cancel`/`incrementNonce` must invalidate an order; partial fills must update `filled`/remaining so the order cannot be over-filled or replayed for the same tranche.
- **Royalty enforcement (EIP-2981).**
  - `royaltyInfo` is advisory — marketplaces may ignore it.
  - A royalty receiver that reverts can DoS a sale; a royalty can be set to 100% or to the zero address.
  - Operator-filter registries have been deprecated and are bypassable via custom transfers or protocol tokens.
- **Marketplace escrow and bid/offer settlement.**
  - Bids are escrowed (WETH or native). Look at accept/cancel/update ordering and collection offers with thresholds.
  - Seller-side payout before NFT transfer (reentrancy); a `buy` that pays an attacker-controlled `recipient`; partial offers that are not tracked.
- **`safeTransferFrom` to malicious receivers.** The hook is the attack entry; a receiver that reverts can block a settlement or airdrop (`vulnerabilities/dos-griefing`).
- **Enumerable / batch-mint DoS.**
  - `ERC721Enumerable` `_allTokens` and `tokenByIndex` are unbounded; `walletOfOwner` iterates the full range.
  - A batch mint or airdrop loop that pushes native value can exceed the block gas limit or revert on one bad receiver.
- **Token id / URI trust.** A `tokenURI` that calls an attacker-controlled base, a URI that changes after sale, or metadata used to price.
- **Mint supply and allowlist.** A public/allowlisted mint whose `maxMint` is per-tx but not per-wallet; a Merkle allowlist not bound to the caller; a mint signature reused across mints.
- **Timed sale / auction settling.** A `block.timestamp` boundary off-by-one; an outbid refund that re-enters; a reserve price that is not enforced.
- **Non-EVM analogue.** Solana Metaplex: collection authority and `verify_collection`, update/freeze authority, and pNFT rule sets. For compressed NFTs (Bubblegum), a Merkle proof, leaf index, and root must be validated on every transfer — a stale or shared root can replay a cNFT (`ecosystems/solana`).

## Where to look

- `safeTransferFrom`, `_safeMint`, `_mint`, `_update`, `onERC721Received`, `onERC1155Received`, `onERC1155BatchReceived`.
- Marketplace `fulfillOrder`, `fulfillAdvancedOrder`, `matchOrders`, `acceptOffer`, `cancel`, `incrementNonce`, `validateOrder`, `_validateOrderParameters`; the order struct and `OrderParameters`.
- `royaltyInfo`, `getRoyalties`, operator-filter checks, `transferFrom` vs `safeTransferFrom` paths.
- Escrow state: `bids`, `offers`, `escrowedAmount`, `filled`, `cancelled`, `nonces`/`counters`, `_verifySignature`.
- Batch/airdrop loops and `ERC721Enumerable` storage (`_allTokens`, `_ownedTokens`), `tokenByIndex`.
- Mint config: `maxSupply`, `mintLimit`, `merkleRoot`, `price`, sale window, and the allowlist proof verification.
- Solana: `verify_leaf`, `mint_v1`/`transfer` Bubblegum instructions, `verify_collection`, pNFT rule sets, freeze/update authority.
- Bid/offer reads: `getBid`, `highestBid`, `offerNonce`, and per-buyer offer mappings.

## Attack plan

1. Find every `safeTransferFrom`/`safeMint` where the recipient is attacker-influenced; draw the reentrancy path and what state is still stale.
2. For each signed order/mint: recompute the digest, then replay it (same marketplace, second contract, fork), forge it, or mutate `s`.
3. Test cancellation and partial fill: fill twice, overfill, or fill after cancel.
4. Attack settlement: front-run accept, re-enter on the receiver hook, or redirect the payout.
5. Check royalty/receiver reverts and operator-filter bypass as DoS or royalty-theft.
6. Force a batch mint/airdrop to exceed gas or revert on one receiver.

## Proof

A Foundry PoC: a malicious receiver that re-enters `mint`/`settle` and mints or drains twice; a replayed
order/mint signature; a partial-fill over-fill; or a batch that consistently reverts. Show concrete
token/value deltas. Without a reachable trace it is a **lead** (`analysis/severity_calibration`).

## Fix / Mitigations

Follow checks-effects-interactions and reentrancy-guard receiver-facing flows; bind every voucher/order to
`chainId`, `verifyingContract`, a consumed nonce, and a deadline; increment a per-maker counter on cancel
and on full fill; enforce partial-fill accounting; handle reverting royalty receivers; treat operator
filters as advisory; avoid unbounded loops with claim/pull patterns and paginated enumeration; on Solana
validate the Merkle root, leaf index, and collection authority per transfer.
