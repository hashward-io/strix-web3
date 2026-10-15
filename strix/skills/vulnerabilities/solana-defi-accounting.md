---
name: solana-defi-accounting
description: Solana DeFi accounting - reserves/balance_of as source of truth, AMM invariant and rounding, Pyth/Switchboard staleness, lending liquidation math, vault share inflation, fees
---

# DeFi Accounting & Oracle Trust (Solana)

On Solana the "balance" of a pool is either a stored field or a live token-account amount, and a
price is an account you chose to trust. Getting either wrong lets an attacker move value without
moving the invariant.

## Where to look

- **Reserve vs live balance** — programs that store a `reserve: u64` and update it separately
  from the SPL token accounts can drift: a direct `spl_token::transfer` into the vault (a
  "donation") changes the real balance but not `reserve`. Conversely, trusting
  `token_account.amount` as the source of truth exposes you to donation/`sync`-style manipulation.
  Decide which is canonical and check every read/write against it. Watch `token_account.amount`
  vs `token_account.delegate`/`delegated_amount` and frozen state.
- **AMM invariant & rounding** — constant-product `x * y = k` (`checked_mul`, `u128` to avoid
  overflow). Check the output formula `out = (in * reserve_out) / (reserve_in + in)`, that fees
  are applied before/after consistently, and that `k` never decreases for the pool. Rounding the
  user's output *up* or the reserve *down* leaks value. `LP` mint/burn share math must round
  against the user. First-liquidity price setting is attacker-controlled (`sqrt(k)`-style).
- **Oracle staleness & confidence (Pyth)** — `pyth_sdk_solana::load_price_feed_from_account_info`
  returns a `PriceFeed`; read `price.price`, `price.expo`, `price.conf`, `price.publish_time`.
  Prefer `get_price_no_older_than(&clock, max_age, &feed_id)` and reject when
  `clock.unix_timestamp - publish_time > max_age` or `conf / |price|` exceeds a bound. `expo` is
  `i32`; ignoring it mis-scales by orders of magnitude. Verify the feed's `feed_id`/`price_account`
  is the expected one — an attacker can pass a different feed.
- **Switchboard** — `switchboard_v2::AggregatorAccountData` / `latest_confirmed_round`
  (`RoundData.result`, `std_dev`, `num_success`, `min_response`). Same staleness/confidence/
  feed-identity checks apply.
- **Lending liquidation math** — health factor / LTV derived from oracle price and decimals;
  check the liquidation bonus, close factor, and whether a manipulated price lets an attacker
  liquidate a healthy position or avoid liquidation. Interest accrual (`borrow_rate` compounding)
  must not round in the borrower's favor repeatedly.
- **Vault share inflation** — ERC-4626-style `shares = assets * total_shares / total_assets`, and
  `assets = shares * total_assets / total_shares`. If `total_shares == 0`, the first depositor can
  donate to inflate the price and make later depositors' shares round to zero (see
  `vulnerabilities/erc4626-inflation`). Guard with a minimum-liquidity seed or virtual offset.
- **Fee accounting** — protocol fee taken from the correct side (input vs output), claimed
  without double-spending, and tracked so it cannot be withdrawn twice. Check `claim_fee`/
  `collect_fees` against the stored fee accumulator.

## Attack plan

1. For each pool/vault, identify the canonical balance: stored field or live `token_account.amount`.
2. Test donation and direct-transfer paths against store-then-read ordering.
3. Recompute the AMM invariant around the fee and rounding; find inputs where `k` drops or output
   rounds in the attacker's favor.
4. For each oracle read, try a stale price, a wide confidence, a wrong `expo`, and a substituted
   feed account.
5. Model first-depositor and subsequent-depositor share math at empty and 1-unit supply.

## Proof

- Anchor: `anchor test` / LiteSVM. Donate directly to the pool token account
  (`spl_token::transfer` from an attacker ATA) then call swap/withdraw and show the attacker's
  take increases beyond the honest AMM output.
- Oracle: use a mock `PriceFeed` account with a stale `publish_time` or fat `conf` and show the
  program accepts it.
- Vault: deposit 1 lamport, donate to inflate, deposit again, show shares round to 0 and the
  victim's deposit is captured.

## Fix

Pick one source of truth and enforce it (or use an internal `balance` synced atomically via the
token program). Apply fees and rounding consistently against the user; compute in `u128` and use
checked math. Validate oracle `feed_id`, `expo`, `publish_time`, and `conf` on every read. Add a
virtual-offset/minimum-liquidity guard to share math. See `vulnerabilities/oracle-manipulation`,
`vulnerabilities/precision-rounding`, `protocols/oracles`, `ecosystems/solana`.
