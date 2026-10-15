---
name: ton
description: TON playbook — FunC and Tact; cells, internal/external messages, sender trust, bounce handling, get-methods, jettons, and the TON bug-class map
---

# TON Ecosystem (FunC & Tact)

TON contracts are async actors passing **cells** (bags of bits). A contract cannot read the blockchain directly; everything arrives as an inbound message and leaves as one or more outbound messages. The two hardest truths: **an internal message's sender is only an address you must validate**, and **bounces are asynchronous**.

## When to use

- A FunC `.fc`/`.func` contract, a Tact `.tact` contract, a Jetton, NFT, or wallet.
- Code using `sender_address`, `recv_internal`/`recv_external`, `send_raw_message`, or get-methods.
- You need the bug-class map before narrowing to `tooling/ton`.

## Message model

- **`recv_internal`:** `(int balance, int msg_value, cell in_msg_full, slice in_msg_body)`. The sender address is parsed from `in_msg_full` — the callee must extract and validate it.
- **`recv_external`:** no sender; used by wallets. It must accept a signed message and reject replays (seqno).
- **There is no global `msg.sender`;** extracting the wrong field or trusting a forwarded sender is the core spoofing bug.
- **`msg_value` vs `balance`:** `msg_value` is the attached TON; the contract must retain enough to pay rent and outbound fees.
- A jetton transfer **forwards `sender_address`** down the chain; the final `transfer_notification` carries the **jetton wallet**, not the original user.

## Cells, bags, depth, and gas

- A cell holds up to 1023 bits and 4 refs; depth is limited (~1024). Fully parsing an attacker-supplied body before any gas check is a **gas bomb**.
- Bounds-check every cell load (`load_uint`, `~load_ref`); a short cell aborts, or silently loads garbage if length is not verified.
- Store the minimum data; use `preload_uint`/`load_bits` deliberately.

## Bounce handling

- A message with `bounce: true` that fails bounces back the remaining value with the original body flagged `bounced`. The sender must handle the bounce to roll back logical state, or the user's balance is debited while tokens are lost.
- **`send_mode` flags:** `+2` (ignore errors), `+64` (carry remaining value), `+128` (carry all balance). The wrong flag drops a bounce or over-sends value.
- Non-bounceable messages to uninitialized contracts vanish; do not assume success.

## Get-methods

- `get_*` methods run **off-chain** (no gas, no state change). They can return anything and **must not be trusted by other contracts** (a contract cannot call a get-method synchronously).
- A get-method that does heavy cell traversal can time out.
- UIs and bots that trust a get-method can be misled if on-chain state is manipulated.

## Jettons and `transfer_notification`

- **Flow:** user → their jetton wallet (`transfer`) → destination jetton wallet → credits and sends `transfer_notification` to the destination owner.
- The **`transfer_notification` `sender_address` is the jetton wallet**, not the user — reading the user from it is spoofable.
- **`forward_payload`/`forward_ton_amount`:** custom data forwarded to the destination; trust nothing in it unless the jetton wallet is verified.
- **`query_id`** correlates async operations; collisions or reuse break request/response matching.
- Verify the jetton master/wallet addresses against expected values before acting.

## Tact specifics

- `message` structs declare the body layout; a mismatch with the opcode/FunC side is type confusion.
- `init` runs on the first inbound message; **an uninitialized contract can be initialized by anyone** if `init` does not verify the sender or opcode.
- `sender()` returns only the parsed sender address.
- Receivers (`receive(msg: X)`) dispatch on opcode/type; a missing receiver drops or aborts the message.

## Toolchain & build

- **FunC:** `func -o out.fif contract.fc stdlib.fc`; Blueprint (`npx blueprint build`) or `toncli`.
- **Tact:** `npx tact` / the `tact` compiler → FunC + ABI.
- **Blueprint** (`npx blueprint test`) and the **sandbox** (`@ton/sandbox`, `@ton/core`) run contracts in-process; craft cells and messages directly.
- `tonviewer`/`tonkeeper` for inspecting deployed contracts.

## Where the bugs live

- **Sender spoofing** — trusting `sender_address` without checking the expected wallet/contract; internal vs external confusion; trusting a forwarded sender.
- **Bounce handling** — not handling `bounced` messages (lost jettons/TON); wrong `send_mode`.
- **Cell depth / gas bombs** — fully parsing an attacker cell before a gas check.
- **Get-method assumptions** — using a get-method for on-chain logic (impossible) or trusting it off-chain.
- **Jetton `transfer_notification` trust** — reading the user from the wallet sender; unverified `forward_payload`.
- **`query_id` collisions** — async request/response mixups.
- **Uninitialized `init`** — anyone initializes the contract.
- **Insufficient value retention** — the contract cannot pay rent/fees and gets frozen.

## Proof standard

A Blueprint/`@ton/sandbox` test that deploys the contract, sends the crafted internal message (spoofed sender, malformed cell, bounce trigger), and asserts the unauthorized withdrawal, lost balance, or state corruption, showing the resulting message tree. A code trace is a **lead**.

## Testing

- `npx blueprint test` with `Sandbox`; craft cells by hand to control the sender field.
- Test bounce paths by sending a message that fails in the destination.
- Test `init` with an unauthorized deployer.
- Simulate low `msg_value` to probe rent/fee behavior.

## Fix patterns

Extract and whitelist `sender_address`; verify jetton wallet/master addresses; handle `bounced` messages and roll back; choose `send_mode` deliberately (`+2` + `+64` for fees); bounds-check every cell load and bound work before parsing; verify `query_id`; restrict `init`; retain a minimum balance; never use a get-method for on-chain logic.
