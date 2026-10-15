---
name: bitcoin
description: Bitcoin Script and Miniscript playbook — opcodes, sighash flags, malleability, timelocks, covenants, ordinals/runes, miniscript, bitcoin-cli/BDK
---

# Bitcoin Script / Miniscript Ecosystem

Bitcoin Script is non-Turing-complete and stack-based, with **no loops and no state**. Security comes from carefully chosen signature-hash flags, timelocks, and the exact script template. Miniscript is a structured subset that compiles to Script and can be analyzed. Auditing here is about **who can spend, under what conditions, and whether the signature covers what you think it does**.

## When to use

- A raw `scriptPubKey`/`scriptSig`, a multisig/timelock/covenant design, or a Miniscript policy.
- A taproot descriptor, a PSBT signer, an ordinals/runes protocol, or a BDK/Rust-Bitcoin integration.
- You need the bug-class map before narrowing to `tooling/bitcoin`.

## Script fundamentals

- Opcodes: `OP_CHECKSIG`/`OP_CHECKSIGVERIFY`, `OP_CHECKMULTISIG(V)`, `OP_HASH160`/`OP_SHA256`, `OP_CLTV` (absolute locktime), `OP_CSV` (relative), `OP_IF`/`OP_ELSE`/`OP_ENDIF`, `OP_DROP`, `OP_DUP`.
- **`OP_CHECKMULTISIG` off-by-one:** it consumes one extra stack item; a malformed script leaves the stack dirty and fails.
- **`OP_RETURN`** is unspendable and used for data (runes/ordinals envelopes).
- Limits: 1000 stack elements, 520-byte pushes, 201 non-push opcodes per script — exceed them and the spend is invalid.
- **P2TR script-path:** `OP_CHECKSIG` for the internal key; `OP_CHECKSIGADD` for tapscript multisig (a different construct with its own bugs).

## Signature-hash flags and malleability

- **SIGHASH flags:** `SIGHASH_ALL` (default, covers all outputs), `SIGHASH_NONE` (no outputs — anyone can redirect value), `SIGHASH_SINGLE` (one output; the "SIGHASH_SINGLE bug" returns a `1` digest for an out-of-range index), `SIGHASH_ANYONECANPAY` (others may add inputs).
- A signature that does not commit to amount/recipient is redirectable.
- **Malleability:** pre-SegWit ECDSA signatures and scriptSig are malleable (a third party changes the txid without invalidating it); rely on SegWit/taproot and never use an unconfirmed txid as a deposit reference.
- Standardness: non-DER and high-S signatures are non-standard (`SCRIPT_VERIFY_LOW_S`, `SCRIPT_VERIFY_DERSIG`).

## Timelocks

- **`OP_CLTV`** (absolute, `nLockTime` semantics; the `<value>` distinguishes height vs time) — a wrong value or a missing `OP_DROP` leaves the stack dirty.
- **`OP_CSV`** (relative to the input's `nSequence`) — requires the spending tx to set `nSequence` correctly; a missing sequence update makes CSVs ineffective.
- The height/time encoding boundary (`500000000`) is easy to get wrong — a timelock that is always satisfied (or never) is a bug.

## Covenants and advanced patterns

- **Covenants** (`OP_CTV`-style or pre-signed tx chains) restrict where funds go; a covenant that under-specifies the output (missing amount or missing scriptPubKey pin) is bypassable.
- **Taproot script trees:** each leaf is a spending path; a leaf the designer thought unreachable is a vulnerability if it is reachable.
- **`OP_CHECKSIGADD` tapscript multisig:** accumulation order and the initial `0`; a dropped signature changes the threshold silently.
- **Anchors/CPFP:** fee-bumping designs that let a third party re-fee or replace a tx.

## Ordinals and runes

- Ordinals use **inscription envelopes** (`OP_FALSE OP_IF ... OP_ENDIF` with `ord` content-type) committing data to a sat; a protocol that trusts envelope content or "the first inscription" is spoofable — anyone can inscribe.
- Runes use `OP_RETURN` with a protocol encoding (`OP_13`-style) and a `Runestone`; the trust model assumes **the first valid runestone** in a tx — a crafted tx with multiple candidates misleads naive parsers.
- Envelope parsing must handle multiple envelopes, pushdata spanning several bytes, and unexpected opcodes.

## Miniscript

- Miniscript is a policy language (`and(pk(A),or(pk(B),after(100)))`) compiling to Script with a defined type/properties (B/V/W, `d`/`u`/`s`/`f`/`e`). Use it to **reason** about spend conditions instead of eyeballing bytes.
- **Compilation must be checked:** `rust-miniscript`/Bitcoin Core compile a policy to a script; a hand-rolled script that drifts from the intended policy is the bug.
- **`Descriptor`s** (`wsh(...)`, `tr(...)`) encode a policy plus keys; a wrong threshold, wrong keys, or a missing `csv`/`cltv` is a policy bug.
- Malleability flags (`s`/`f`/`e`) matter for tx pinning.

## Toolchain & build

- `bitcoin-cli` (`decodescript`, `getdescriptorinfo`, `createmultisig`, `testmempoolaccept`, `sendrawtransaction`, `analyzepsbt`).
- `bitcoin-tx` for raw txs; `bdk`/`rust-bitcoin` for descriptor wallets; the `miniscript` crate for policy compilation.
- `bitcoind -regtest` for local testing.

## Where the bugs live

- **Script/Miniscript covenant soundness** — under-specified outputs; a leaf more permissive than intended.
- **Signature-hash flags** — `NONE`/`SINGLE` misuse; a signature not covering outputs/amount.
- **Malleability** — txid-based accounting without SegWit/taproot; third-party scriptSig edits.
- **Timelock semantics** — CLTV/CSV value or `nSequence` errors; the height/time boundary.
- **Ordinals/runes envelope trust** — trusting the first/only envelope; parser divergence across implementations.
- **Taproot/tapscript** — `CHECKSIGADD` threshold errors; unreachable-leaf assumptions.
- **PSBT** — a signer that signs an under-specified input; missing `witness_utxo`/`non_witness_utxo` allows fee/fraud.

## Proof standard

A `regtest` (`bitcoind -regtest`) reproduction: build the spending transaction, submit it, and show it succeeds (or fails) contrary to the intended policy — a covenant bypass, a stale-timelock spend, or a malleated txid. For Miniscript, a `Descriptor` round-trip plus a script-path spend that violates the policy. A static script reading is a **lead**.

## Testing

- `bitcoin-cli -regtest` (`generatetoaddress`, `sendrawtransaction`, `testmempoolaccept`).
- Miniscript policy → descriptor → script, then check `descriptor.script_pubkey()` matches the policy.
- BDK integration tests for descriptor wallets; PSBT sign/analyze round-trips.
- Fuzz envelope/runestone parsers with malformed inputs.

## Fix patterns

Pin every covenant output (scriptPubKey + amount); use `SIGHASH_ALL` (or an explicitly intended flag) so signatures commit to outputs; rely on SegWit/taproot for malleability; set `nSequence` correctly for CSV and encode CLTV values in the documented range; verify tapscript thresholds and `CHECKSIGADD` accumulation; parse all envelopes/runestones defensively and enforce the protocol's "first valid" rule; specify PSBTs fully; express policies in Miniscript and verify the compiled script.
