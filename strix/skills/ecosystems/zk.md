---
name: zk
description: ZK circuit audit playbook — Circom, Noir, Halo2, gnark; under-constrained signals, range checks, soundness, Fiat-Shamir, trusted setup
---

# ZK Circuits as Audited Artifacts

A ZK circuit is a program with two obligations: **completeness** (an honest prover can prove true statements) and **soundness** (a cheating prover cannot). Most circuit bugs are violations of soundness — a constraint that should pin a signal but does not. Read the circuit the way you read a verifier, not a "smart contract".

## When to use

- A Circom `.circom`, Noir `.nr`, Halo2 (Rust), or gnark (Go) circuit; a prover/verifier pair; an on-chain proof verifier.
- Code that generates or verifies proofs, hashes, Merkle trees, range checks, or fixed-point arithmetic inside a circuit.
- You need the bug-class map before narrowing to `tooling/circom` or `tooling/noir`.

## The core mental model

- A circuit enforces constraints. A signal in the witness but in **no constraint** is unconstrained — the prover sets it to anything. This is the dominant bug.
- Witness generation (the "hint") is **nondeterministic code the prover runs**; it does not constrain. Soundness must come from constraints, not hints.
- Public inputs are the statement; everything else is the prover's choice.

## Circom

- `signal input`/`signal output`; `template`/`component`; linear vs non-linear constraints. A template emitting fewer constraints than expected is a red flag.
- **`<--` (assignment) vs `<==` (constraint):** `<--` computes a witness value **without constraining it** — every `<--` must be paired with an explicit `===`, or the value is free.
- **`===`** constrains equality **mod p**, not over integers.
- **Range checks:** prove an n-bit value with `Num2Bits(n)`/`LessThan`; a raw `<--` for a boolean is unsound.
- **`assert`** is a witness-time check and does **not** constrain; it only fails the honest witness generator.
- An unused output of a component does not constrain that component's internals unless its inputs are constrained.

## Noir

- `fn main(...) -> pub ...`; `Field` is a prime field; `u8..u128`, `bool`, arrays, structs.
- **`constrain`** enforces equality; a value returned but never constrained is a hint.
- **`unconstrained fn`** runs only in the witness generator — never trust its result; verify with constraints.
- Arrays have compile-time sizes; a length inferred from input is a soundness problem.
- `nargo test` for witness tests; `nargo prove`/`nargo verify`; `nargo check` for type/constraint errors.

## Halo2

- The `Circuit` trait's `configure` (columns, selectors, gates) and `synthesize` (assignments). Bugs live in **gate definitions**: a custom gate whose selector is not enforced, or a gate that under-constrains a cell.
- A cell assigned but constrained by no gate is free — check every copy-constraint and equality-constraint.
- Lookup arguments (`lookup`/`LookupTable`) for range checks: verify the table covers the range and the argument is enabled.
- `MockProver` (`halo2::dev::MockProver`) checks witness satisfiability and reports unconstrained cells where possible.

## gnark

- Go; `frontend.Circuit` with `frontend.Variable`; `api.AssertIsEqual`, `api.AssertIsLessOrEqual`, `api.Select`.
- **`api.AssertIsBoolean`** is required before using a `Variable` as a boolean, else it is not restricted to {0,1}.
- Range checks need a bit-width for the bound; a variable bound is itself unconstrained.
- Groth16/PLONK backends; watch `api.Println`/debug-only constraints and field-wrapping arithmetic.

## Soundness primitives

- **Under-constrained signals** — the dominant class; a signal in no constraint.
- **Missing range checks** — a field element used as an index/amount without `Num2Bits`/range.
- **Fiat–Shamir / transcript** — the challenge must bind **all** public inputs and prior commitments; omitting one lets the prover choose it after the challenge. Check hash/transcript ordering.
- **Trusted setup** — Groth16 needs a ceremony; leaked toxic waste breaks soundness. PLONK/STARK universal setups differ — know which.
- **Nondeterminism / hints** — unconstrained computations.
- **Aliasing** — the same field element reused across logically distinct values.
- **Zero-knowledge leaks** — a public output revealing a private input; debug prints in the prover.

## Toolchain & build

- **Circom:** `circom circuit.circom --r1cs --wasm --sym`; **`snarkjs`** (`groth16 setup/prove/verify`, `zkey`); `circomspect` (static), `ecne` (under-constrained-signal analysis), `picus`.
- **Noir:** `nargo test`/`prove`/`verify`/`check`/`info` (constraint counts); `bb` (Barretenberg) backend.
- **Halo2:** Rust crate; `MockProver` in tests; `halo2_proofs`/`halo2-lib`.
- **gnark:** Go; `test.NewAssert(t).Prover(...)`.

## Where the bugs live

- **Under-constrained signals** — `<--` without `===`; a Noir value never `constrain`ed; a Halo2 cell with no gate.
- **Missing range checks** — field arithmetic used as integers.
- **Soundness/completeness** — a constraint set that admits false statements, or rejects true ones.
- **Fiat–Shamir / transcript** — unbound inputs, wrong challenge order.
- **Trusted setup** — ceremony provenance; `zkey` reuse across circuits.
- **Nondeterminism/hints** — trusting `unconstrained`/hint output.
- **Public-input handling** — a private input leaked as public; a public input not bound into the proof.
- **On-chain verifier** — a public-input count/order mismatch, or a `verifyProof` that ignores its result.

## Proof standard

A test demonstrating the soundness break: for Circom/Noir, a crafted witness/proof for a **false** statement that verifies (or a true statement that fails); for on-chain, a Foundry test calling the verifier with the bad proof and asserting it should revert. A `circomspect`/`ecne` lead without a witness is a **lead**, not a finding.

## Testing

- `circomspect circuit.circom` and `ecne` for under-constrained-signal leads.
- `snarkjs` end-to-end: setup → prove → verify with a manually crafted witness.
- `nargo test` for witness/constraint unit tests; `nargo info` for constraint counts.
- `MockProver` in Halo2 to find unconstrained cells; gnark test assertions.
- Negative tests: a witness that must fail verification.

## Fix patterns

Replace `<--`/unconstrained assignments with full constraints; add explicit range checks (`Num2Bits`, `AssertIsBoolean`, `AssertIsLessOrEqual`); bind every public input into the Fiat–Shamir transcript in a fixed order; constrain hint outputs; keep secrets private and outputs minimal; audit the ceremony and pin the `zkey`; verify the on-chain verifier's public-input count and treat a `false` result as failure.
