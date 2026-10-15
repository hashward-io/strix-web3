---
name: zk-soundness-completeness
description: ZK soundness and completeness — malleable proofs, missing constraints, field over/underflow, assert vs constraints, verifier input and proof/statement binding
---

# Soundness and Completeness

**Soundness** means no false statement can be proven. **Completeness** means every true statement can be. A circuit or verifier that trades away soundness for convenience is exploitable; one that is incomplete breaks honest users. This skill is about making the proof bind to the right statement.

## Where to look

- **Missing constraints that enable a forged witness.** When you prove "the inputs satisfy R" but constrain only part of R (e.g. constrain `sum(a_i) === total` but not each `a_i`'s range), a prover picks a witness satisfying the partial relation. Enumerate each claimed property and its constraint.
- **Partial binding of derived values.** A hash/commitment output constrained at one point but used unconstrained elsewhere; a Merkle root checked but the leaf not constrained.
- **Proof malleability.** A proof that verifies should not be re-encodable into a different valid proof for the same statement (replay/relay). Check verifier code that does not fully bind every proof element, and schemes with known malleability (some Groth16/SnarkJS settings, missing negations, unbound commitments). If the on-chain consumer uses the proof as a unique id, malleability yields replay.
- **Field over/underflow.** The proving field is prime, so subtraction is `a + (p - b)` and "negative" is `p - x`. A circuit that assumes integer semantics gets `p - 1` where it wanted `-1`. Constrain absolute values / ranges explicitly; do not rely on wrap-around behaving like two's complement.
- **Field division.** Division is multiplication by an inverse and only defined for nonzero divisors; a circuit that divides by a signal that can be zero produces a garbage (or unconstrained) value.
- **`assert` vs constraints.** In **Circom**, `assert(cond)` is a **compile-time** check on `var` values and is **not** a constraint — use `===`. In **Noir**, `assert(cond)` does generate constraints in a constrained context (but not inside `unconstrained fn`). Confusing the two leaves a property unchecked on-chain while it "passes the test".
- **Verifier input handling.** The generated `verifier.sol` / `Groth16Verifier` takes public signals in a fixed order. A consumer that concatenates or reorders inputs, pads them, or reads them from an untrusted source binds the proof to the wrong statement.
- **Public-signal count / order.** Confirm the vector passed to `verifyProof` matches the circuit's `main` public order exactly; an off-by-one silently shifts every signal.
- **Proof/statement binding.** The public inputs must include everything the statement depends on (amounts, recipient, chain id, contract address, nonce). A missing domain field means a proof for one context verifies in another (cross-chain / cross-contract reuse).
- **Replay across instances.** A proof valid for one contract/pool accepted by another that shares the verification key but not the domain binding.
- **Verifier `verifyProof` return handling.** A wrapper that ignores the boolean return, or treats a revert as success, accepts invalid proofs.

## Attack plan

1. Write down the exact statement each circuit is supposed to prove, then map each clause to a constraint.
2. Find any clause with no constraint (a soundness hole) or any constraint that rejects a true statement (a completeness bug).
3. Check field-arithmetic assumptions: negative values, comparisons, division, overflow.
4. Inspect the verifier call site: public-signal order, values, and whether a domain/context field is bound.
5. Test malleability: take a valid proof and mutate its encoding; does it still verify?
6. Reuse a proof in a different context (different recipient/chain/contract) and check it is rejected.

## Proof

The strongest evidence is a **forged witness** that satisfies every constraint yet proves a false statement, verified with `snarkjs groth16 verify` (Circom) or `nargo prove` + `bb verify` (Noir). For malleability, show a mutated proof that verifies. For completeness, show an honest witness that is rejected. For binding, show a proof accepted in the wrong context. Include the verifier output; a soundness claim without a forged witness is a **lead**.

## Fix

Constrain every clause of the statement; add boolean/range constraints; avoid integer assumptions over the field. Replace verification-time assumptions with explicit public inputs (bind amount, recipient, domain, chain id). Use a non-malleable verification routine and treat the proof as non-unique unless the statement binds a nullifier/nonce. Follow the generation tool's exact public-signal order and check `verifyProof`'s return.

## Variants and adjacent bugs

- **Malleable proof** — a re-encoded proof still verifies.
- **Partial constraint** — a property of the statement left unconstrained.
- **Wrong-field arithmetic** — integer assumptions in a prime field.
- **`assert` that is not a constraint** — Circom compile-time `assert`.
- **Cross-context replay** — a proof accepted where it should not be.

## Do not flag

- Constraints that fully bind every public input and derived value.
- Verifiers that check `verifyProof`'s return and bind a domain separator.
- Proofs treated as non-unique when a nullifier/nonce is bound.

## Leads vs findings

- A missing constraint is a **lead**; the forged witness or replayed proof is the finding.
- Show the verifier accepting a false statement with `snarkjs` or `nargo`+`bb`.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/zk` — proving-system model.
- `tooling/zk-circom` — `circom` and `snarkjs` prove/verify.
- `vulnerabilities/zk-underconstrained-circuit` and `vulnerabilities/zk-setup-and-fiat-shamir`.
