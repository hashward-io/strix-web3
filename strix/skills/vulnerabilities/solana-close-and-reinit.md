---
name: solana-close-and-reinit
description: Solana account close and reinit bugs - closing without zeroing data, revival attack, rent reclamation, reinitialization after close, Anchor close semantics
---

# Account Close & Reinitialization (Solana)

Closing an account means zeroing its data and moving its lamports out; because Solana has no
tombstone, a closed account can be **revived** by sending lamports back, and re-**initialized**
if the program uses `init`. Both are reachable by design unless the program defends them.

## Where to look

- **Close without zeroing data** — a handler that only drains lamports
  (`**account.try_borrow_mut_lamports()? = 0`) but leaves the account data intact. The account
  survives (lamports can be re-added within the same transaction) and still deserializes as
  valid state.
- **Anchor `close` and the revival attack** — Anchor's `#[account(close = destination)]` sets
  `CLOSED_ACCOUNT_DISCRIMINATOR` (`[255; 8]`), zeroes the data, and transfers lamports to the
  destination. Before that discriminator existed (Anchor < ~0.25) close left a live account;
  the "revival attack" re-funded it in the same transaction and reused it. Verify the Anchor
  version and that every close path uses the constraint rather than manual lamport moves.
- **`init` after `close`** — if closing does not clear the discriminator/data, `#[account(init,
  seeds = ..., bump)]` on the same PDA in a later transaction (or the same one) can be re-run
  because the account still "exists". A program that reinitializes must require the account be
  empty (`data_is_empty` / `lamports == 0`) or that the discriminator be the closed sentinel.
- **Rent reclamation** — closing only reclaims rent if the account is truly removed (lamports
  hit zero *and* data zeroed); partial drains leave a rent-exempt-but-dead account. `Rent::get()`
  / `Rent::minimum_balance(space)` define the threshold; draining below it makes the account
  garbage-collected, above it leaves a live husk.
- **Reinitialization of a live account** — `init` on an account that already holds data with the
  right owner; check `#[account(init, payer = ..., space = ...)]` cannot target an existing
  funded account (Anchor's `init` uses the system program `create_account`, which fails if the
  account already has data/lamports — but a hand-rolled `create_account`/`allocate` may not).
- **`realloc` to zero** — shrinking with `realloc(..., false)` does not zero the trailing bytes;
  a later `realloc` back up exposes stale data.
- **Close authority / destination control** — `close = destination` where `destination` is
  attacker-chosen sends the reclaimed rent to the attacker.

## Attack plan

1. For every close path, determine whether data is zeroed and the discriminator set.
2. Check whether the account can be re-funded in the same transaction and then reused by any
   instruction that does not reject the closed sentinel.
3. Check whether `init` can run against an existing (revived) account.
4. Verify rent math: does the program leave the account rent-exempt or truly empty?
5. Confirm the close destination is fixed/authorized.

## Proof

- Anchor: `anchor test`. In one transaction: close the account, then `system_program::transfer`
  lamports back to the same address, then call an instruction that borrows it. If it succeeds,
  revival is live.
- LiteSVM:

```rust
let mut svm = LiteSVM::new();
svm.add_program_from_file(program_id, "target/deploy/prog.so")?;
// tx1 closes `vault`; tx2 re-funds it; tx3 reuses it as if open
let txs = [close_tx, refund_tx, reuse_tx];
for tx in txs { svm.send_transaction(tx)?; } // reuse_tx succeeding => finding
```

A `solana-program-test` sequence across three transactions is a complete reachable trace. Name
the discarded lamports and the reused stale field.

## Fix

Use `#[account(close = destination)]` so data is zeroed and the sentinel discriminator is set;
reject accounts whose discriminator is `CLOSED_ACCOUNT_DISCRIMINATOR`; require
`data_is_empty()`/zero lamports before re-`init`. Zero on `realloc` shrink. Fix the close
destination to the owner or a program PDA. See `ecosystems/solana`, `tooling/solana-anchor`,
`vulnerabilities/solana-account-validation`.
