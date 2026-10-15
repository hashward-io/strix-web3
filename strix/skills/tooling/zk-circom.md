---
name: zk-circom
description: Circom toolchain — circuit compile with r1cs/wasm/sym, snarkjs Groth16 and PLONK setup/prove/verify, and circomspect/ecne/picus analysis
---

# Circom (zk-SNARK circuits)

Circom compiles arithmetic circuits to R1CS; `snarkjs` performs the trusted setup and proof generation and verification. Soundness bugs live in the constraints, not the control flow.

## Install / build

- `npm install -g circom` or `cargo install circom` (Rust `circom`); check `circom --version`.
- `npm install -g snarkjs`; `snarkjs --version`.
- Analyzers: `cargo install circomspect`; build `ecne` and `picus` from `github.com/Veridise`.
- Circuit libraries: `npm install circomlib` (and `circomlib-matrix`).

## Core commands

```bash
# compile
circom circuit.circom --r1cs --wasm --sym -o build/
circom circuit.circom --c --prime bn128          # C++ witness generator
snarkjs r1cs info build/circuit.r1cs
snarkjs r1cs print build/circuit.r1cs build/circuit.sym
snarkjs r1cs export json build/circuit.r1cs circuit.json

# powers of tau (trusted setup)
snarkjs powersoftau new bn128 14 pot12_0000.ptau -v
snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau --name="1" -e="random"
snarkjs powersoftau prepare phase2 pot12_0001.ptau pot12_final.ptau -v

# groth16
snarkjs groth16 setup build/circuit.r1cs pot12_final.ptau circuit_0000.zkey
snarkjs zkey contribute circuit_0000.zkey circuit_0001.zkey --name="1" -e="random"
snarkjs zkey export verificationkey circuit_0001.zkey verification_key.json
snarkjs groth16 fullprove input.json build/circuit_js/circuit.wasm circuit_0001.zkey proof.json public.json
snarkjs groth16 verify verification_key.json public.json proof.json
snarkjs zkey export solidityverifier circuit_0001.zkey verifier.sol

# plonk
snarkjs plonk setup build/circuit.r1cs pot12_final.ptau circuit.zkey
snarkjs plonk prove circuit.zkey build/circuit_js/circuit.wasm input.json proof.json public.json
snarkjs plonk verify verification_key.json public.json proof.json

# static analysis
circomspect circuit.circom
ecne --r1cs build/circuit.r1cs
picus --r1cs build/circuit.r1cs
```

## Audit workflow

1. Compile with `--r1cs --wasm --sym`; `snarkjs r1cs info` shows constraint, signal, and input counts.
2. Read every `<==`, `<--`, and `===`: a `<--` (witness assignment) with no matching constraint is **under-constrained** — the classic Critical.
3. Verify all signals feeding comparisons/`Num2Bits` are range-checked; an unconstrained `lessThan` result is a lead.
4. Run `circomspect`, `ecne`, and `picus` for leads; treat them as hints, then hand-trace.
5. Reproduce an under-constraint with a malicious `input.json` that satisfies the constraints but forges a false statement.
6. Check the trusted-setup transcript and that the deployed verifier matches the exported key.

## Pitfalls

- `snarkjs` proving does not prove the circuit is sound — only that a witness matches the constraints.
- `<--` for division/modulo is convenient but unsafe without an explicit constraint tying it back.
- PLONK uses a universal setup and custom gates; Groth16 needs a circuit-specific ceremony.
- A verifier contract generated from the wrong `zkey` rejects valid proofs (or accepts forged ones on a mismatch).
- See `ecosystems/zk` and `hacking_agents/invariant` for the reasoning discipline around constraint completeness.
