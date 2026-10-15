---
name: fizz-invariants
description: Generate and run a Foundry/Echidna/Medusa invariant-fuzzing suite from the protocol's invariant catalog
---

# Fizz — Invariant Fuzzing

Turn the invariant catalog (`analysis/invariant-discovery`) into properties and break them with a stateful fuzzer.

## Process

1. **Harvest invariants.** Start from `analysis/invariant-discovery`. For every invariant, record its **kind** (conservation, bound, ratio, state machine, temporal, cross-contract, economic) and the **actors** involved. Include the function's own guards — `require` and exact-revert checks are invariants that fuzzing can falsify.
2. **Inspect existing tests.** If the repo already has a fuzzing suite, extend it; do not duplicate. Match its handler and actor conventions.
3. **Generate the highest-value classes first** (these catch real bugs):
   - **Conservation** — `total == Σ parts`; handler sums tied to the same on-chain state.
   - **Bound** — `withdrawal ≤ depositable`, `≤ maxDeposit`, `≤ protocol-payable`.
   - **Arithmetic** — every subtraction path (`ΔA = ΔB - x`) with overflow risk.
   - **One-shot** — latch/state-machine integrity.
   - Specific state-machine and economic invariants from the catalog.
4. **Build a handler.** Wrap the target with handler functions that call the real entry points with bounded actors and amounts (`bound`/`between`). Without a handler, the fuzzer may not reach the protocol's own invariants.
5. **Assert the base conditions up front.** Add the boundary conditions (a minimum op count, a non-trivial state) as district preconditions where the tool lets you; when it does not, install them as explicit preconditions.

## Running

- **Foundry:** `forge test --match-contract Invariant` (`foundry_invariant` tests, `targetContract` handlers).
- **Echidna:** `echidna . --contract <Handler> --config echidna.yaml` (`tooling/echidna`).
- **Medusa:** `medusa fuzz` (`tooling/medusa`).

Run multiple tools — they break different properties.

## Reporting

- A failing property is a **confirmed** invariant break — the strongest automated signal. Port the counterexample to a Foundry PoC (`custom/foundry-poc`) and report it, citing the invariant, the sequence, and the impact.
- A clean run is **evidence**, not proof: state the tool, config, `testLimit`, `seqLen`/`callSequenceLength`, and which invariants had no property (and why).
- Record coverage gaps: functions the harness never reached mean the invariant may be untested.
