---
name: cardano-datum-redeemer-context
description: Cardano datum, redeemer and script context bugs - trusting inline or hashed datum, attacker-chosen redeemer, misread script context, validity range, and required signers
---

# Datum, Redeemer & Script Context (Cardano)

A Cardano validator receives three attacker-influenced inputs: the **datum** attached to the UTxO, the **redeemer** the spender supplies, and the **script context** (the whole transaction). Treating any of them as trusted — or misreading the context's validity range, signers, or purpose — is a recurring high-severity bug.

## Where to look

- **`spend(datum, ...)` with `Option<Data>`** — a missing datum, or a datum whose fields are never re-validated against the expected schema.
- **Inline vs hashed datum** — with a hash-only datum the content is not in the transaction; with an inline datum the spender can present any content the script only half-checks.
- **Redeemer selectors** — a sum-type redeemer not exhaustively matched, or a numeric action not range-checked.
- **Script context reads** — broad `list.any`/`list.find` over `self.inputs`/`self.outputs`, or reading an input that may only be a reference input.
- **Validity range** — `self.validity_range` compared with the wrong `aiken/interval` helper (`is_entirely_after`, `is_entirely_before`, `contains`), or left unbounded so the script runs at an unintended time.
- **Required signers** — `self.extra_signatories` (the transaction's required signers) not checked, or checked for the wrong key; a datum that claims an owner without that owner signing.
- **Plutus V2 vs V3** — V3's `Transaction` adds `redeemers`, `voting_procedures`, and `proposals`; code ported between versions can read fields whose meaning changed.
- **Withdraw-zero / purpose** — a staking `withdraw` handler (or an unguarded `mint`/`certify`) invoked with a zero amount to run code or satisfy another script.

An illustrative shape where the datum is believed without checking the signer:

```aiken
spend(datum: Option<Data>, _redeemer: Data, _ref: OutputReference, self: Transaction) {
  expect Some(owner) = datum          // attacker controls this
  True                                // never checks self.extra_signatories for owner
}
```

## Attack plan

1. For each handler, list the datum/redeemer/context fields it reads and what it validates.
2. Supply a datum the script accepts at the type level but that encodes an unauthorized owner, amount, or deadline.
3. Craft the redeemer to select the branch with the weakest checks; test every constructor.
4. Set the validity range to bypass a time lock; set required signers to a key the attacker controls and confirm the script still accepts.
5. Reuse the same script hash under a different purpose and check whether the handler distinguishes them.
6. Check V2↔V3 ported code for fields that changed meaning.

## Proof

- `aiken test`: construct the context with the malicious datum/redeemer/validity range and assert the handler returns `Ok`.
- Show the honest transaction errors and the malicious one succeeds — that difference is the finding.
- For time/signature bugs, assert the accepted transaction would move value or mint tokens it should not.

```aiken
test attacker_datum_without_signature_is_accepted() {
  let tx = tx_with_extra_signatories([])      // owner did not sign
  is_ok(vesting.spend(Some(attacker_owner_datum), unit, ref, tx))
}
```

## Fix

Re-validate every datum field against the expected schema and require an inline datum, matching on it explicitly. Exhaustively match the redeemer and reject unknown constructors. Bound the validity range with the correct `aiken/interval` helper and require the transaction to fall inside the intended window. Require the owner in `self.extra_signatories`, and remember it reflects required signers rather than the raw transaction signer set. Forbid the withdraw-zero purpose unless it is intended. See `ecosystems/cardano` and `hacking_agents/trust-gap`.

## See also

- `ecosystems/cardano` — script-context shape and handler models.
- `vulnerabilities/cardano-eutxo-double-satisfaction` — output and continuation checks.
- `vulnerabilities/cardano-value-and-minting` — value and policy checks.
- `hacking_agents/access-control`, `hacking_agents/trust-gap` — authorization and assumed trust.
