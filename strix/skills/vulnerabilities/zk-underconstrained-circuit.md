---
name: zk-underconstrained-circuit
description: ZK under-constrained circuits — missing boolean/range checks, <-- without constraints, dead constraints, unconstrained public inputs, circomspect/picus detection
---

# Under-Constrained Circuits

A circuit proves what its **constraints** permit, not what the source code appears to compute. Any signal the witness can set freely — because no constraint ties it to the intended relation — lets a malicious prover forge a witness. Under-constraining is the dominant ZK bug class.

## Where to look

- **`<--` assignment without a constraint.** In Circom, `out <-- expr;` computes a witness value with **no** constraint; `out <== expr;` constrains it. The dangerous idiom is `out <-- f(x);` **without** a following `out === f(x);`. Grep every `<--`.
- **Missing boolean checks.** A signal treated as a bit but not constrained to `{0,1}`. The constraint is `s * (s - 1) === 0;`. Flag any selector, flag, or comparator output lacking it.
- **Missing range checks.** Values used as indices, bit decompositions, or comparisons must be range-bounded. `Num2Bits(n)` emits `n` bits plus a recomposition check `sum(b_i * 2^i) === in`; a hand-written decomposition often omits the bits-are-boolean constraints or the recomposition.
- **Signed handling.** A "negative" value in a field is `p - x`; without an explicit sign bit and range check, comparisons and magnitudes are wrong.
- **Dead / vacuous constraints.** A `===` that is trivially satisfiable, constrains a signal never connected to any output, or has both sides sharing the same unconstrained variable. `circom --inspect` reports non-quadratic or redundant constraints.
- **Unconstrained public inputs.** A signal in the `main` public list that no constraint uses (or only one satisfiable trivially). The verifier then accepts proofs for a statement that does not bind it.
- **Template misuse.** Instantiating a component but not wiring its inputs/outputs (`comp.in <== x;` missing, so `comp.in` floats), reusing a template with different semantics, or copying a component and dropping a constraint. Circom does not require all inputs be connected.
- **Aliasing / signal reuse.** The same signal serving two roles where one use constrains and the other does not; a witness computed one way and used another.
- **`var` vs `signal` confusion.** A `var` is compile-time and generates no constraints; if an auditor assumes a `var` computation is proven, it is not.
- **Import/shadowing bugs.** A local signal shadowing an input name so the input is never constrained; renamed includes that change a template's arity.
- **Overly permissive `signal input` lists.** An input that is declared but only used in a hint (not a constraint) is effectively public and unconstrained.

## Attack plan

1. Enumerate every signal and classify it: constrained by an equation, tied to an input/constant, or free.
2. For each `<--`, confirm a matching `===`. For each computed signal, confirm it feeds a constraint.
3. Check every signal used as a boolean/index has a boolean/range constraint.
4. Verify each `main` public input is actually constrained to the statement.
5. Check each template instantiation connects all inputs and consumes all relevant outputs.
6. Run static and formal tools (below) and triage each warning.

## Detection tooling

- `circomspect path/to/circuit.circom` (Trail of Bits linter) — reports under-constrained signals, unconstrained outputs, and common constraint omissions.
- `picus --r1cs circuit.r1cs` (formal under-constrained detection, install on demand) — proves a signal is constrained by no equation, or finds witnesses violating the intended relation. (`ecne` is unmaintained; do not rely on it.)
- `circom circuit.circom --r1cs --wasm --sym --inspect` — emits the R1CS plus an inspection report of non-quadratic/degenerate constraints.
- `snarkjs r1cs info circuit.r1cs` — constraint/input/wire counts; a suspiciously low count hints at dropped constraints.

## Proof

A working **unconstrained witness** is the standard: a malicious prover that satisfies all constraints while producing an out-of-spec output (e.g. a value the honest witness could never take). Show the concrete witness, the `snarkjs` (or `nargo`/`bb`) prove+verify, and the verifier accepting it. Testing the honest path passing is **not** proof; the forged witness is. A `circomspect` warning with no forgery stays a **lead**.

## Fix

Replace every free assignment with a full constraint (`out <== f(x)` or `out === f(x)`). Add boolean constraints (`s * (s - 1) === 0`) and `Num2Bits` range checks with recomposition. Ensure every public input is bound. Wire all template inputs. Re-run `circomspect` clean, and add negative tests that attempt a forged witness.

## Variants and adjacent bugs

- **`<--` without `===`** — a free witness value.
- **Missing boolean** — a bit not constrained to `{0,1}`.
- **Missing range** — `Num2Bits` without recomposition or boolean checks.
- **Dead constraint** — a `===` disconnected from any output.
- **Template misuse** — unwired component inputs.

## Do not flag

- `<--` followed by a matching `===` on the same signal.
- Range checks via `Num2Bits` with recomposition and boolean constraints.
- Constraints that only look redundant but are load-bearing.

## Leads vs findings

- A `circomspect` warning is a **lead**; the forged witness is the finding.
- Show the out-of-spec witness accepted by `snarkjs groth16 verify`.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/zk` — Circom/Noir/Halo2/gnark model.
- `tooling/zk-circom` — `circom`, `snarkjs`, `circomspect`.
- `vulnerabilities/zk-soundness-completeness` — forged witnesses and binding.
