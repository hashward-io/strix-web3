---
name: medusa
description: Medusa stateful fuzzer — foundry-compatible Solidity invariant fuzzing with coverage guidance and call sequences
---

# Medusa

Medusa is a go-ethereum-based stateful fuzzer, Foundry-compatible. Where Foundry's `invariant` runs in-process, Medusa runs in an EVM and produces long, coverage-guided call sequences — often reaching states Foundry's fuzzer misses.

## Setup

```json
// medusa.json
{
  "fuzzing": {
    "workers": 8,
    "testLimit": 0,
    "callSequenceLength": 100,
    "targetContracts": ["Vault"],
    "corpusDirectory": "corpus"
  },
  "compilation": { "platform": "foundry" },
  "testing": { "stopOnFailedTest": false }
}
```

Run: `medusa fuzz` (or `medusa fuzz --config medusa.json`). It reuses Foundry's `test/` invariant contracts and `targetContract`/handler conventions.

## Writing targets

- Any contract with `invariant_*` functions (Foundry `Test` style) is fuzzed.
- Use handler contracts to restrict actor addresses and bound arguments (same idea as Echidna).
- `function invariant_conservation() public` reverts on violation; Medusa reports the call sequence.

## Medusa vs Echidna

- Medusa is coverage-guided and generally faster with multiple workers; good at deep sequences.
- Echidna is more mature on some property semantics and asset filtering.
- Run **both** on the invariant catalog for confidence; they break different properties.

## Workflow

1. Start from the invariant catalog (`analysis/invariant-discovery`).
2. Generate the harness (`custom/fizz-invariants`).
3. `medusa fuzz`; on a failure, take the printed sequence.
4. Minimize (`--shrink` in Foundry terms; Medusa emits a Foundry `test_repro`-style sequence) and port to a PoC.

## Signals

- A failing `invariant_*` is a confirmed break — strongest class of automated signal.
- Coverage reports tell you which functions were never reached — a harness gap, not a clean bill.
- A long run with no failure is evidence bounded by the config; state the `testLimit`/`callSequenceLength`.
