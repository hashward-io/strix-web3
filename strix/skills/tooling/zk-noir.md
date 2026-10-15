---
name: zk-noir
description: Noir toolchain — nargo new/build/test/execute/prove/verify, Prover.toml and Verifier.toml, Barretenberg bb backend, and Solidity verifier integration
---

# Noir (Aztec)

Noir is a Rust-like DSL for zk circuits using the Barretenberg UltraPlonk backend; `nargo` drives building, proving, and verification. The compiler enforces constraints, so bugs are usually unconstrained inputs or missing `assert`s.

## Install / build

- `curl -L https://raw.githubusercontent.com/noir-lang/noirup/main/install | bash && noirup`; check `nargo --version`.
- Backend `bb` (Barretenberg): `curl -L https://raw.githubusercontent.com/AztecProtocol/aztec-packages/master/barretenberg/bbup/install | bash && bbup`.
- The standard library ships with `nargo` (`std::`); extra dependencies go in `Nargo.toml`.
- Solidity verifier: `bb write_solidity_verifier` from a verification key.

## Nargo.toml / layout

```toml
[package]
name = "my_circuit"
type = "bin"
authors = [""]

[dependencies]
```

- Layout: `Nargo.toml`, `src/main.nr` (circuits and `fn main`), `Prover.toml` (private and public inputs), `Verifier.toml` (public inputs written by `nargo execute`).

## Core commands

```bash
# project / build
nargo new my_circuit
nargo check                 # type/constraint check without proving
nargo build                 # compiles to target/*.json (ACIR)
nargo fmt

# test / execute
nargo test                  # runs #[test] functions
nargo execute witness       # runs main with Prover.toml, writes target/witness.gz

# prove / verify (Barretenberg)
bb prove -b ./target/my_circuit.json -w ./target/witness.gz -o ./target
bb write_vk -b ./target/my_circuit.json -o ./target
bb verify -k ./target/vk -p ./target/proof

# solidity verifier
bb write_solidity_verifier -k ./target/vk -o ./target/Verifier.sol

# legacy nargo prover (deprecated in favor of bb)
nargo prove
nargo verify
```

## Audit workflow

1. `nargo check` then `nargo test` — a compiling circuit is the baseline; `#[test]` functions are the specification.
2. Read `fn main` inputs: distinguish private (`Prover.toml`) from public (returned) values, and confirm which are constrained.
3. Hunt **unconstrained** witnesses — values assigned with `let` that never appear in an `assert`/comparison; the missing constraint is the PoC.
4. Check `assert` placement, field/`u` integer overflow semantics, and array-index bounds.
5. Verify the public-input set matches what the Solidity verifier exposes — see `ecosystems/zk`.
6. Reproduce with `nargo execute` on a malicious `Prover.toml` that satisfies the circuit but breaks the intended statement.

## Pitfalls

- Noir arithmetic is over a prime field; `u8`/`u32` methods (`overflowing_*`) must be used explicitly to detect wrap.
- `nargo prove`/`verify` are moving toward `bb`; version skew between `nargo`, `bb`, and the Solidity verifier breaks verification.
- A `#[test]` that only checks a valid witness does not test soundness; add negative tests.
- Public inputs in `Verifier.toml` are not automatically wired into an on-chain verifier — check the integration.
- `nargo fmt` changes source but not semantics; still diff it so edits are intentional.
