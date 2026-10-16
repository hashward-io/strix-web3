---
name: ton-security-checklist
description: TON security checklist — message sender identity, bounce and state, cells and gas, jettons, get-methods and async replies
---

# TON Security Checklist

A checklist for reviewing TON contracts (FunC, Tact, Tolk). TON is **asynchronous and message-driven**: a contract reacts to inbound messages, and every send is a separate message that may bounce. The distinctive bugs are **sender identity**, **bounce handling**, and **cell/gas** mismanagement.

## Sender identity & permissions

- [ ] **Trusting the sender address** — authorizing on `sender_address()` without checking it is the expected wallet/contract, or trusting a `forward` payload's claimed origin (`vulnerabilities/ton-sender-and-bounce`).
- [ ] **Spoofed `op` / payload** — dispatching on an attacker-controllable opcode or body without an authorization check.
- [ ] **Initialization front-running** — an uninitialized contract that any caller can `init`, or an owner field set by the first message.

## Bounce & state

- [ ] **Ignoring the bounce flag** — a send that can bounce but whose state was already committed (funds credited before confirmation).
- [ ] **Non-bounceable sends losing funds** — `send_raw_message` with mode flags that drop value on failure.
- [ ] **Reentrancy via async messages** — state assumed final in the same transaction when the reply arrives in a later block.
- [ ] **Unchecked jetton transfer acknowledgement** — crediting a deposit before the jetton `transfer_notification` is observed (`vulnerabilities/ton-jetton-and-getmethods`).

## Cells, compute & gas

- [ ] **Cell overflow** — building a cell beyond its bit/ref limits, or unbounded data in one cell (`vulnerabilities/ton-cell-and-gas`).
- [ ] **Gas draining / out-of-gas** — an attacker-triggered path that consumes the contract's balance or blocks the message.
- [ ] **Get-method trusted as state** — a get-method's result (off-chain) assumed to match on-chain state at execution time.

## Jettons & tokens

- [ ] **Wallet/owner confusion** — the jetton master trusts a caller or a `sender` that is not the wallet it must verify.
- [ ] **Mint/burn authorization** — minting without an owner check, or a burn that crediting logic trusts.

## Validation

- [ ] Reproduce with `@ton/sandbox` (Blueprint) or `@ton-community/test-utils`: spoof a sender, trigger a bounce, send a gas-draining message, or replay an async flow, asserting the unauthorized state change.
- [ ] Run `tact`/`func` build and inspect the resulting message flow (`blueprint`) before trusting the deploy.
