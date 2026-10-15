---
name: bitcoin-script-covenants
description: Bitcoin Script/Miniscript covenants — CLTV/CSV bounds and units, sighash flags and malleability, multisig mistakes, ordinals/runes envelope trust, dust/relay assumptions
---

# Bitcoin Script Covenants

A covenant is a script that constrains where coins can go next. Its soundness rests on timelock semantics, signature-hash coverage, threshold encoding, and relay policy — each of which has subtle units and defaults that silently weaken the constraint.

## Where to look

- Timelocks: `OP_CHECKLOCKTIMEVERIFY` (BIP65) and `OP_CHECKSEQUENCEVERIFY` (BIP112) in the script; the transaction's `nLockTime` and each input's `nSequence`.
- Signature flags: the sighash byte in the signature (`SIGHASH_ALL` 0x01, `SIGHASH_NONE` 0x02, `SIGHASH_SINGLE` 0x03, `SIGHASH_ANYONECANPAY` 0x80) and any `OP_CODESEPARATOR`.
- Multisig / threshold: `OP_CHECKMULTISIG` (the extra dummy element), `OP_CHECKSIGADD` / Taproot `multi_a` and `thresh`, and `miniscript` policies.
- Envelope / metadata: `OP_FALSE OP_IF ... OP_ENDIF` inscription envelopes, runes `OP_RETURN` protocols, and code that parses them.
- Policy: `scriptPubKey` type, dust threshold, minimum relay fee, and `OP_RETURN` size limits.

## Units and defaults (get these wrong and the covenant is void)

- `OP_CLTV` compares the top stack item to `nLockTime` and requires the *same locktime type* (both < 500000000 = block height, both >= = UNIX time). Different types make CLTV fail; the wrong operand makes it a no-op guarantee.
- `OP_CSV` compares against `nSequence` in BIP68 units: bit 22 (`0x400000`) selects time-based (units of 512s) vs block-based; bit 31 disables the check entirely. A `nSequence` with the disable bit set makes CSV pass unconditionally.
- A covenant that only includes CLTV/CSV but does not encode a *minimum* bound, or places the operand as `0`, gives no timelock protection.
- `OP_CHECKMULTISIG` pops one extra dummy element; leaving it off (or a wrong `m`/`n`) makes the spend fail or the policy weaker than intended.

## Attack plan

1. Decode every script (`bitcoin-cli decodescript`, `decoderawtransaction`) and identify the covenant predicate. Ask what it *allows*, not what it forbids.
2. Timelock bypass: check whether the CLTV/CSV operand type matches `nLockTime`/`nSequence` type, whether the disable bit is set, and whether the operand is a real lower bound. A mismatched type or a `0` operand permits spending earlier than intended.
3. Missing locktime coupling: CLTV needs the tx's `nLockTime` to be set and the input's `nSequence` not `0xffffffff` (which disables nLockTime). A covenant that checks CLTV but where the spender sets `nSequence = 0xffffffff` cannot enforce it.
4. Sighash malleability: a signature with `SIGHASH_NONE`/`SINGLE` covers fewer outputs/inputs, so a third party can alter the rest of the transaction. Check every signature's sighash flags — a covenant relying on `SIGHASH_ALL` semantics while a signer uses `ANYONECANPAY` is bypassable.
5. `OP_CODESEPARATOR`: shifts the scriptCode the signature commits to; a signature that does not cover the covenant's key constraint can be reused elsewhere.
6. Multisig/threshold: verify the number of pubkeys, the threshold, and key ordering; a `2-of-3` that is actually `1-of-3` due to a wrong `m`, or a threshold policy in Miniscript that compiles weaker than written.
7. Envelope trust: an output or witness that *looks* like an inscription/runes envelope is just bytes. Code that treats "contains an ordinal envelope" as proof of a real asset is trusting attacker-controlled data (ordinals/runes are not consensus-validated application state).
8. Dust/relay: an output below the dust threshold is non-standard and will not relay; a covenant that pays a dust amount to a key path cannot be spent on the network. `testmempoolaccept` reveals it.

## Proof

- Regtest via `bitcoin-cli`: build the transaction, `testmempoolaccept`, and `sendrawtransaction`. Show a spend that the covenant was written to forbid but that is accepted, or a valid spend that is rejected as non-standard.
- Use `decodescript` / `decoderawtransaction` to display the exact operands, types, and sighash flags.
- For Miniscript policies, compile with `rust-miniscript` (or the `MINS`/`miniscript` tool) and compare the compiled script to the intended policy.

## Fix

- Match CLTV/CSV operand types to the actual locktime/sequence type; encode explicit minimum bounds; never use a `0`/disable operand.
- Ensure `nLockTime`/`nSequence` are set consistently with the timelock and cannot be overridden (`nSequence != 0xffffffff`).
- Pin sighash flags to `SIGHASH_ALL` (or a deliberate flag) for every signature that must commit to the covenant; avoid `OP_CODESEPARATOR` unless intended.
- Verify multisig `m`/`n`, key order, and Taproot thresholds against the intended policy.
- Treat inscription/runes envelopes as untrusted data; validate assets against protocol rules, not byte patterns.
- Keep outputs above the dust threshold and above minimum relay fee; test with `testmempoolaccept`.

## Severity and finding bar

- A covenant that permits spending earlier than intended is **High** to **Critical** (funds released).
- A sighash/malleability gap that lets a third party redirect funds is **Critical**.
- A non-standard (dust/below-relay) covenant output is **Medium**, **High** if it locks principal.
- Envelope trust that mislabels attacker data as an asset is **Medium** to **High** depending on downstream value.

## See also

- `ecosystems/bitcoin` — the ecosystem playbook.
- `vulnerabilities/signature-replay`, `vulnerabilities/logic-flaws` — the general classes.
- `ecosystems/evm` — for cross-chain covenant/bridge reasoning.
