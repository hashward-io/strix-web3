---
name: halmos
description: Halmos symbolic execution — prove or falsify Solidity assertions and invariants symbolically with bounded model checking
---

# Halmos

Halmos is a symbolic (bounded model checking) engine for Solidity, Foundry-compatible. Where fuzzers find counterexamples by luck, Halmos either **proves** a property for all inputs within a bound or returns a **concrete counterexample**.

## Usage

- `halmos` — run all test functions symbolically.
- `halmos --function test_exploit` — target one function.
- `halmos --loop 4` — allow up to N loop iterations (default small; increase for loops).
- `halmos --solver-timeout-assertion 60000` — per-assertion timeout.
- `halmos --storage-layout` — inspect slot layout.

## Writing symbolic tests

- Use `function check_X() public` (or `test_` with `--function`) and symbolic inputs. Halmos treats free variables and function arguments as symbolic.
- Assert the invariant:

```solidity
function check_no_free_shares(uint256 amount) public {
    vm.assume(amount < MAX);
    // ...
    assert(vault.totalShares() == sumBalances());
}
```

- A returned `Counterexample` block gives the exact inputs — port it to a PoC.

## When to use

- **Math and arithmetic** where a property should hold for all inputs (rounding, bounds, conservation) — Halmos either proves it or gives the input that breaks it.
- **Access control** — prove that a privileged function is unreachable for `msg.sender != owner`.
- **Small, bounded hypotheses.** Symbolic execution explodes on unbounded loops and external calls; keep the property local and bounded.

## Interpreting results

- **Proof** (no counterexample within the bound) is strong but bounded — state the bound (`--loop`) and the assumptions (`vm.assume` constraints are part of the claim).
- **Counterexample** is a concrete finding — reproduce it in a Foundry test.
- **Timeout / unknown** is not proof of safety; record it as an open gap.

## Pitfalls

- Over-constraining with `vm.assume` proves a weaker property; list your assumptions.
- External calls and unbounded loops make it diverge; isolate the pure math.
