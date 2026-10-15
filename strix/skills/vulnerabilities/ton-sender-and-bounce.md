---
name: ton-sender-and-bounce
description: TON sender trust and bounce handling — internal vs external messages, sender_address spoofing, my_address checks, bounced fund loss, and external replay
---

# TON Sender Trust and Bounces

A TON contract has two entrypoints, `recv_internal` and `recv_external`, and in both the "sender" is attacker-influenced data on the wire. Treating a forwarded address field as authenticated, or ignoring the `bounced` flag, is how TON contracts lose funds.

## Where to look

- Entrypoints: `recv_internal`, `recv_external`, and Tact handlers `receive()` / `receive(msg: X)`.
- The message header. In FunC, `in_msg_full` starts with `int_msg_info$0 ihr_disabled:Bool bounce:Bool bounced:Bool src:MsgAddress ...`. In Tact, `sender_address` is the parsed `src`.
- Any address read from the **body** rather than the header: a forwarded payload, an `owner` / `dest` argument, `response_destination`, or a jetton `forward_ton_amount` recipient.
- Bounce control: the `bounceable` flag on sends, the `bounced` flag on receipts, and send modes `SEND_MODE_BOUNCE_ON_ACTION_FAIL` and `SEND_MODE_IGNORE_ERRORS`.
- Identity helpers: `my_address()`, `my_address().hash`, `equal_slices(a, b)`, `parse_std_addr`, `parse_var_addr`.
- External-message auth: `seqno`, `valid_until`, and the stored public key the signature is verified against.

## Attack plan

1. Map every field the code treats as an authenticated sender. If it is loaded from `in_msg_body`, an attacker chooses it. Only `src` in the header is authoritative.
2. Spoof `sender_address`. Send a body claiming to originate from the owner, jetton master, or a relay. If the contract compares a body field to a stored address instead of the real `src`, authorization is bypassed.
3. Confirm owner-gated code uses `equal_slices(sender, owner)` on the header sender — never on a body-supplied `from`.
4. Bounce loss. Drive a bouncing message that performs work, then force a throw. The outbound bounce refunds the value, but the state writes already made are not reverted unless the handler checks `bounced` or the code deliberately `commit()`s. Example: credit a deposit, then throw → user is refunded by the bounce *and* keeps the credited balance.
5. `bounced` handling. A returned bounce arrives as an internal message with `bounced = -1`. If the handler does not check it, bounce-service logic can be re-triggered with attacker-controlled bodies.
6. Sending to a non-bounceable address, or with `SEND_MODE_IGNORE_ERRORS`, silently destroys value. A withdraw path that lets the user set `bounceable = false` can burn protocol funds.
7. External replay. If `recv_external` accepts a signed message without checking a monotonic `seqno` / `valid_until`, a captured external message replays. Also check `accept_message()` is not called before signature verification (gas griefing).

## Message model quick reference

```func
() recv_internal(int balance, int msg_value, cell in_msg_full, slice in_msg_body) impure {
    slice cs = in_msg_full.begin_parse();
    int flags = cs~load_uint(4);              ;; bit0 = bounced
    slice sender = cs~load_msg_addr();        ;; authoritative src
    if (flags & 1) { return (); }             ;; never apply the original transition on a bounce
    ;; ... only now read/trust in_msg_body
}
```

## Proof

- Blueprint / Sandbox PoC (`@ton/blueprint`, `@ton/sandbox`, `npx blueprint test`): build a fake internal message with a crafted body `sender` and assert the unauthorized action succeeds.
- Or drive a sequence where an operation throws *after* it mutates storage, then show the bounce refunded value while storage still holds the credit.
- Show the exact message fields (`bounce`, `bounced`, `src`) and storage before/after.
- For external replay, send the same signed external message twice and show the second is accepted.

## Fix

- Authenticate on the header `src` only; every body-carried address is untrusted input.
- Verify `equal_slices(sender, expected)` (or Tact `sender_address`) at each privileged entry, including bounce handlers.
- Handle `bounced` explicitly: treat it as a refund/failure notification and never re-apply the original state transition. Use `commit()` only when the state must persist across a deliberate throw.
- Set `bounceable` intentionally on outbound value sends; default to bounceable for contracts.
- Require a monotonic `seqno` and a `valid_until` on external receivers, and verify the signature before `accept_message()`.

## See also

- `ecosystems/ton` — the ecosystem playbook.
- `vulnerabilities/access-control`, `vulnerabilities/accounting-conservation` — the general classes this specializes.
- `ton-cell-and-gas`, `ton-jetton-and-getmethods` — sibling TON surfaces.
