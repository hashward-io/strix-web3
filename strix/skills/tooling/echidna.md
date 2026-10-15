---
name: echidna
description: Echidna property-based fuzzer — config, property functions, invariants, and assert-mode for Solidity
---

# Echidna

Echidna is a property-based (invariant) fuzzer. You write Solidity properties; Echidna tries to break them with random call sequences, including the attacker's favorite sequences.

## Setup

```yaml
# echidna.yaml
testMode: assertion        # or property
testLimit: 50000
seqLen: 100
contractAddr: "0x00a329c0648769A73afAc7F9381E08FB43dBEA72"
deployer: "0x10000"
sender: ["0x10000", "0x20000", "0x30000"]
balanceContract: 0
cryticArgs: ["--foundry-compile-all"]
```

Run: `echidna . --contract TestContract --config echidna.yaml`.

## Writing properties

- **Assertion mode:** `assert(condition)` inside any function; Echidna tries any call sequence that makes it fail.
- **Property mode:** functions named `echidna_*` returning `bool` that must **always** return `true`.

```solidity
// invariant: total shares equal the sum of balances
function echidna_shares_conserved() public view returns (bool) {
    return vault.totalSupply() == handlerSumBalances();
}

function echidna_solvent() public view returns (bool) {
    return vault.totalAssets() >= vault.totalDeposits();
}
```

## Best practices

1. **Use a handler contract.** Wrap the target so Echidna's random calls hit the real entry points with sensible arguments (bound addresses/amounts to real actors). Without a handler, fuzzing is blind.
2. **Bound inputs.** `amount = between(amount, 0, MAX)`; use fixed actor addresses, not random EOAs.
3. **Start from the invariants** (`analysis/invariant-discovery`): one property per invariant, especially conservation and solvency.
4. **Clamping.** `_clamp`/`_between` to keep requests in range; return early on zero to avoid wasted calls.
5. **Reduce to a counterexample.** Once Echidna finds a violation, it prints the call sequence — minimize it (`--shrink-limit`) and port it into a Foundry PoC (`custom/foundry-poc`).

## Signals vs noise

- A failing property is a **strong** signal — treat it as a confirmed invariant break.
- A property that never fails over a large `testLimit` is evidence, not proof; state the limit and the property.
- Timeouts / compile errors mean the harness is wrong, not the code clean.

## When to use

Invariant-heavy or math-heavy logic where a finding is a broken property rather than a single wrong line: vaults, lending, AMMs, reward accounting, state machines (see `custom/fizz-invariants`).
