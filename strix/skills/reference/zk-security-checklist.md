---
name: zk-security-checklist
description: ZK circuit security checklist — under-constrained signals, soundness/completeness, Fiat–Shamir, trusted setup, and privacy leaks
---

# ZK Circuit Security Checklist

A checklist for reviewing ZK circuits and proving systems (Circom, Noir, Halo2, gnark). The dominant bug is the **under-constrained signal**: a witness value that no constraint pins, so a malicious prover can choose it. Distilled from zkSecurity's *zk-skills* (Circom auditor) and the circulated ZK audit checklists.

## Constraints and witness

- [ ] **Under-constrained signal** — a witness/`<--` assignment with no paired constraint. Prevent: constrain every witness; a computed witness must be pinned by an `===`.
- [ ] **`<--` without a constraint** — the classic Circom footgun. Prevent: follow every `<--` with an equality constraint.
- [ ] **`assert` instead of a constraint** — `assert` is not a constraint and does not bind the proof. Prevent: use `===` for anything the verifier relies on.
- [ ] **Missing booleanity** — a selector/flag not constrained to `0`/`1`. Prevent: `x * (x - 1) === 0`.
- [ ] **Missing range checks** — a value used as an index/amount without a bit decomposition. Prevent: `Num2Bits`/`Bits2Num_strict` with explicit bounds.
- [ ] **Limb bounds** — limbs of a big-number representation not individually bounded, enabling aliasing. Prevent: bound each limb and comparator input.
- [ ] **Comparator inputs** — a comparator that assumes inputs are already in range. Prevent: range-check the inputs.
- [ ] **Selector / mux constraints** — a multiplexer whose selector does not enforce exactly-one branch. Prevent: constrain selectors and the sum.

## Arithmetic in the field

- [ ] **Field wraparound** — values wrapping mod `p` and later interpreted as integers. Prevent: bound values well below `p`.
- [ ] **Division / inverse** — a division used without a nonzero check and multiplication pin. Prevent: check the divisor and pin `a === b * c`.
- [ ] **Aliasing** — two different witnesses satisfying the same constraints, yielding an unintended value.

## Soundness and completeness

- [ ] **Soundness** — can a cheating prover produce an accepting proof for a false statement? Attack the constraints.
- [ ] **Completeness** — can an honest prover be rejected (DoS)? Check boundary inputs.
- [ ] **Public input binding** — public inputs not bound to the private witness/action. Prevent: tie inputs to the statement.
- [ ] **Nullifier / replay** — a nullifier that can be reused or that is not bound to the action. Prevent: domain-separated nullifiers.
- [ ] **Intent binding** — a proof valid for a different action/chain/recipient than intended. Prevent: include domain, chain id, and action in the statement.

## Fiat–Shamir and transcript

- [ ] **Missing/incomplete transcript** — a challenge derived without hashing all public inputs. Prevent: absorb every public value before the challenge.
- [ ] **Challenge reuse / domain separation** — the same challenge across rounds or protocols. Prevent: distinct domain separators.
- [ ] **Weak hash** — a non-collision-resistant hash in the transcript. Prevent: a standard cryptographic hash.

## Trusted setup

- [ ] **Toxic waste** — the setup's secret not destroyed. Prevent: a multi-party ceremony; verify the transcript.
- [ ] **Powers/tau correctness** — a malformed or unverifiable setup. Prevent: verify the setup.
- [ ] **Universal vs circuit-specific** — wrong parameters for the circuit.

## Privacy / zero-knowledge

- [ ] **Metadata leak** — public inputs or transaction shape revealing the private witness.
- [ ] **Nondeterminism/hints** — a hint leaking or being trusted for a private value.
- [ ] **Witness in the clear** — logging or transmitting the witness outside the prover.

## Testing

- [ ] Write a **malicious-prover** test per constraint: try to satisfy the circuit with a wrong witness.
- [ ] Fuzz witness generation; run differential tests of the verifier.

## Sources

- zkSecurity zk-skills (Circom auditor): https://github.com/zksecurity/zk-skills
- Companion skills: `analysis/invariant-discovery`, `custom/fizz-invariants`, `vulnerabilities/signature-replay`.
