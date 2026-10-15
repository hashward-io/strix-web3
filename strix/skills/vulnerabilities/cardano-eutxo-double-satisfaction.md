---
name: cardano-eutxo-double-satisfaction
description: Cardano eUTxO double satisfaction and missing continuation checks - one output satisfying several validators, unvalidated continuing UTxO, output ordering and batching
---

# Double Satisfaction & Continuation (Cardano)

In the eUTxO model a validator is a pure function over the whole transaction, so two independent script inputs can both find the *same* output and each conclude its requirement is met. This **double satisfaction** — and the related failure to validate the continuing UTxO — is the signature Cardano bug class.

## Where to look

- **`self.outputs` scans** — `list.any`, `list.find`, `list.filter` looking for "an output that pays me". A `find` that succeeds says nothing about *which* input it belongs to.
- **`expect ... = self.outputs |> list.at(n)`** — output indices are attacker-controlled; never assume ordering.
- **Missing continuation** — a `spend` handler that returns `True` (or an unrelated output) without asserting a new output at the script address with the expected value and datum.
- **Value checks** — `value.quantity_of` / `value.without_lovelace` run against an output the attacker supplied.
- **Batched spends** — N inputs of the same script consumed while fewer than N satisfying outputs are created.
- **Co-executed scripts** — a validator that trusts the mere presence of another script action (`mint`, `withdraw`) to authorize it.

A typical vulnerable shape:

```aiken
// Every input finds the same "pays the seller" output and accepts.
spend(_datum: Option<Data>, _redeemer: Data, _ref: OutputReference, self: Transaction) {
  expect Some(_out) =
    self.outputs
      |> list.find(fn(out) { value.quantity_of(out.value, policy, asset) >= price })
  True
}
```

## Attack plan

1. List every output property the handler requires (pay X to address A, keep datum D, hold token T).
2. Ask whether the requirement names the *input* it corresponds to. If not, any one output can satisfy it.
3. Consume two or more script UTxOs in one transaction and create a single output meeting the requirement; each input's validator independently accepts it.
4. For continuation bugs: spend a state UTxO and recreate it with a different datum, value, or address; if the validator only checks that *an* output exists, the state is corrupted.
5. Reorder the transaction's outputs and confirm an index-based `expect` still passes.
6. Batch: give a buyer many cheap UTxOs of the same script and buy once.

## Proof

- `aiken test`: build a `Transaction` with two script inputs and one satisfying output; assert the spend handler returns `Ok` for each input.
- Assert the harm numerically: two inputs consumed, one output produced, the attacker's balance up.
- A working test upgrades a lead to a finding; an unproven suspicion is only a **lead**.

```aiken
test one_output_satisfies_two_inputs() {
  let tx = attacker_tx_with_two_inputs_and_one_output()
  // both spend handlers see the same output and accept
  is_ok(swap.spend(Some(d1), r1, ref1, tx))
    && is_ok(swap.spend(Some(d2), r2, ref2, tx))
}
```

## Fix

Require exactly as many satisfying outputs as inputs consumed, and bind each output to its input — carry the spent `OutputReference` in the continuing datum, or require the output value to decrement by exactly the input's contribution. Never rely on output order; match on the output's datum (`Output.datum`) rather than its index. Fully validate the continuing UTxO: address, value (minus `self.fee`), and updated datum.

## See also

- `ecosystems/cardano` — the eUTxO model and validator layout.
- `vulnerabilities/cardano-datum-redeemer-context` — datum/context trust that amplifies double satisfaction.
- `vulnerabilities/cardano-value-and-minting` — value and token checks on the outputs.
- `hacking_agents/invariant`, `hacking_agents/asymmetry` — conservation and input/output mismatches.
