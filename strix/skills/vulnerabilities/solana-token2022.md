---
name: solana-token2022
description: Token-2022 extension bugs - transfer hooks and fees, confidential transfers, permanent delegate, mint/freeze authority misuse, interest/non-transferable mints, program id confusion
---

# Token-2022 Extensions (Solana)

SPL Token-2022 keeps the Token program's interface but adds extensions that change transfer
semantics. A protocol written against Token semantics silently breaks when a 2022 mint enables
transfer fees, a transfer hook, a permanent delegate, or a freeze authority.

## Where to look

- **Program id confusion** — `spl_token::ID` is `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`;
  `spl_token_2022::ID` is `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`. A program constrained to
  the legacy id (`anchor_spl::token::ID`) rejects 2022 mints, or accepts them when it should not.
  In Anchor prefer `Interface<'info, TokenInterface>`, `InterfaceAccount<'info, Mint>` and
  `InterfaceAccount<'info, TokenAccount>` to accept either deliberately.
- **Transfer hooks** — `spl_token_2022::extension::transfer_hook`. The mint can name a
  `TransferHook` program id plus `validation_pubkey`; every `TransferChecked` invokes that
  program, which receives the source, mint, destination, authority and (usually) *your*
  accounts. A malicious hook is **arbitrary CPI / reentrancy** (see
  `vulnerabilities/solana-cpi-safety`). If you pass extra accounts to it, it can mutate them.
- **Transfer fees** — `spl_token_2022::extension::transfer_fee`. `TransferChecked` debits the
  full amount but credits `amount - fee`. `calculate_transfer_fee`/`TransferFee::calculate_fee`
  show the withheld amount. Code that assumes `received == sent` mis-accounts.
- **Confidential transfers** — `extension::confidential_transfer`. Balances are encrypted and
  the account may have `ConfidentialTransferAccount` with an auditor key; you cannot read `amount`
  directly, and `ConfidentialTransfer`/`ApplyPendingBalance` instructions change accounting.
  Blindly trusting `token_account.amount` returns the *pending* plaintext, not the true balance.
- **Permanent delegate** — `extension::permanent_delegate`. A stored delegate can transfer or
  **burn** from any account of the mint without the owner's signature. A protocol holding such
  tokens can be emptied by the delegate.
- **Mint / freeze authority misuse** — a mint with a live `mint_authority` can inflate supply;
  a live `freeze_authority` can freeze user token accounts and lock withdrawals. Check the
  protocol does not rely on a token being unfreezable.
- **Interest-bearing & non-transferable mints** — `extension::interest_bearing_mint` changes the
  reported amount over time (`AmountToUiAmount`); `extension::non_transferable` mints reject all
  transfers. `default_account_state` can default new accounts to frozen.
- **Also worth checking** — `mint_close_authority` (mint can be closed), `cpi_guard`,
  `memo_transfer`, `metadata_pointer`, and `extension::immutable_owner`. Enumerate
  `get_extension_types` / `BaseStateWithExtensions::get_extension_types` on the mint.

## Attack plan

1. For every token the protocol touches, determine whether the mint is legacy or 2022 and which
   extensions are enabled.
2. If a transfer hook exists, who owns the hook program and which accounts does it receive.
3. Recompute amount math assuming a transfer fee, or a permanent-delegate burn.
4. If balances are confidential, check accounting that reads `.amount`.
5. Try to swap the mint/token program id to a 2022 variant (or a fake) your constraints allow.

## Proof

- Anchor: `anchor test` with a `token_2022` mint configured with the extension (Token-2022
  provides helpers in the `spl_token_2022` test utilities / `token-2022` CLI). Show the protocol
  crediting more than it received (fee), or the hook re-entering (hook).
- CLI sanity: `spl-token create-token --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb
  --transfer-fee 100 5000`, then a transfer showing the fee.
- LiteSVM: add the Token-2022 program, create the extended mint, and observe the mis-accounting.

## Fix

Validate the mint's extensions before trusting it; use `Interface`/`InterfaceAccount` to accept
2022 intentionally and reject hooks/fees you do not support. Account for transfer fees explicitly
(`calculate_transfer_fee`). Never assume unfreezable/unmintable/unburnable — check authorities
are `None` or program-owned. See `ecosystems/solana`, `tooling/solana-anchor`.
