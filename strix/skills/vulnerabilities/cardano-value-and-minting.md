---
name: cardano-value-and-minting
description: Cardano value and minting-policy bugs - counterfeit native tokens, non-normalized Value maps, non-one-shot minting, missing lovelace or min-UTxO checks, and locked funds
---

# Value & Minting (Cardano)

Cardano's `Value` is a nested map and native tokens are identified by a `PolicyId`; a minting policy that is not one-shot can print tokens at will. Value bugs are usually a validator checking the *wrong* thing about an output's value or a policy's minted amount.

## Where to look

- **`value.quantity_of(v, policy, name)` vs raw map access** — only `quantity_of` (and `value.flatten`) normalizes the nested `PolicyId -> AssetName -> Int` map correctly; direct `Value` equality or hand-rolled sums miscount.
- **ADA is policy `#""`, asset name `#""`** — code that treats the empty policy as "no token" or skips lovelace arithmetic miscounts value.
- **Counterfeit tokens** — a check on the asset name (or a truncated policy id) instead of the exact `PolicyId`; an attacker mints the same name under their own policy.
- **`self.mint`** — the minted/burned value; a policy that checks `mint` is non-empty but not the exact quantity or policy id.
- **One-shot minting** — the policy does not consume a specific seed UTxO (`OutputReference`), so it can mint repeatedly.
- **Output value** — `output.value` not compared to the input value minus fee; missing minimum-ADA/min-UTxO, producing an unspendable output.
- **Locked funds** — creating an output at the script address with a datum the script will never accept.

An illustrative counterfeit check (name only, any policy):

```aiken
mint(_redeemer: Data, _policy: PolicyId, self: Transaction) {
  // Wrong: an attacker can mint the same asset name under their own policy.
  let (_, _, qty) = self.mint |> value.flatten |> list.find(fn(t) { t.2nd == asset })
  qty > 0
}
```

## Attack plan

1. For each value assertion, confirm it uses `value.quantity_of` (normalized) and the exact `PolicyId`.
2. Try to satisfy the check with a token of the same asset name but a different policy, or with zero/negative quantities.
3. For a minting policy, test whether it is one-shot; if not, mint more than intended in a later transaction.
4. Mint a negative amount (burn) where the code only checks magnitude or sign.
5. Drive an output below minimum-ADA and confirm the script accepts an unspendable output.
6. Compare the output value to the input value minus `self.fee` to find value created or destroyed.

## Proof

- `aiken test`: build a context whose `mint` carries the counterfeit policy or the wrong amount, and assert the policy handler returns `Ok`.
- For value bugs, assert the producing transaction's `output.value` via `value.quantity_of` and show the balance the attacker gains.
- For a non-one-shot policy, mint twice in one transaction or across two transactions and assert both succeed.

```aiken
test counterfeit_token_mints_free_value() {
  let tx = tx_minting_under_attacker_policy(1_000_000)
  is_ok(my_policy.mint(unit, attacker_policy_id, tx))
}
```

## Fix

Use `value.quantity_of`/`value.flatten` for every token comparison and match the exact `PolicyId` and asset name (ADA is `#""`/`#""`). Make minting policies one-shot by consuming a specific seed `OutputReference`. Assert the exact minted quantity and honor the burn sign. Enforce minimum-ADA/min-UTxO on every produced output and compare output value to input value minus `self.fee`.

## See also

- `ecosystems/cardano` — `Value` shape and the minting model.
- `tooling/aiken` — `aiken test` and the `value` helpers.
- `vulnerabilities/cardano-eutxo-double-satisfaction`, `vulnerabilities/cardano-datum-redeemer-context` — sibling eUTxO surfaces.
- `hacking_agents/math-precision`, `hacking_agents/economic-security` — value math and token economics.
