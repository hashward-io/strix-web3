---
name: zk-setup-and-fiat-shamir
description: ZK trusted setup and Fiat-Shamir — toxic waste, vk binding, transcript ordering, wrong-field challenges, weak commitment randomness, snarkjs vk trust
---

# Trusted Setup and Fiat–Shamir

Proof soundness depends on secrets that must be destroyed (the trusted setup) and on a transcript that must bind every commitment before any challenge is derived. Get either wrong and proofs can be forged off-protocol, independent of the circuit.

## Where to look

- **Trusted setup / toxic waste.** Groth16 and similar need a per-circuit setup whose trapdoor (`tau`, `alpha`, `beta`, `gamma`, `delta`) must be destroyed. If the toxic waste survives anywhere, an attacker can forge proofs for **any** statement. Check the provenance of `.zkey`/`proving_key`/`verification_key` and the Powers-of-Tau source.
- **Ceremony parameter binding.** The verification key must be bound to the exact circuit (R1CS). A verifier deployed with a vk from a different circuit — or a vk with a substituted parameter — validates the wrong relation.
- **Setup reuse.** Using one `.zkey` for two different R1CS files, or a universal-setup (Plonk/Halo2) SRS that is stale or not the one intended.
- **Fiat–Shamir transcript ordering.** Challenges must be derived **after** every relevant commitment is appended. If a challenge is squeezed before a commitment, the prover chooses the commitment to make the challenge favorable (the classic frozen-heart / weak-FS attack). Audit the order of `transcript.append` vs `transcript.challenge` (Halo2, PlonK, custom FS).
- **Challenge over the wrong field / domain.** Hashing into the wrong modulus (e.g. reducing mod the base field `p` instead of the scalar field `q`, or vice versa) breaks soundness or creates collisions.
- **Missing domain separation.** No round/circuit/instance tags lets a challenge from one round or circuit be reused in another.
- **Weak randomness in commitments.** A blinding factor that is zero, constant, low-entropy, or seeded from a public value makes commitments non-hiding and/or lets the prover bias the FS challenge.
- **`snarkjs` verification-key trust.** The vk embedded in the deployed verifier contract is the root of trust. Verify it matches the audited circuit's vk, is not updatable by an attacker, and that the deployed `verifyProof` uses exactly this vk.
- **Updatable verifier state.** A contract whose vk/config is owner-mutable can have its root of trust swapped after deployment.
- **Preprocessing determinism.** Non-deterministic setup output (different vk per run) that is not pinned lets a compromised setup go unnoticed.

## Attack plan

1. Trace the setup artifacts: who ran the ceremony, was the toxic waste destroyed, and does `snarkjs zkey verify` pass against the Powers-of-Tau?
2. Compare the deployed vk against the circuit's exported vk byte-for-byte.
3. For each Fiat–Shamir interaction, list the append order and confirm no challenge precedes a commitment.
4. Check the challenge field/modulus and the presence of domain separators between rounds and circuits.
5. Inspect commitment blinding: source, entropy, reuse.
6. Attempt an off-protocol forgery if a trapdoor or FS ordering flaw is reachable.

## Detection tooling

- `snarkjs zkey verify circuit.r1cs powersOfTau.ptau circuit.zkey` — validates the setup against the ceremony.
- `snarkjs zkey export verificationkey circuit.zkey vk.json` — the vk to compare against the deployed verifier.
- `snarkjs powersoftau verify powersOfTau.ptau` — checks the ceremony transcript.
- `snarkjs r1cs info circuit.r1cs` and `circomspect` — circuit-level issues that compound with setup flaws.

## Proof

For a setup flaw, demonstrate an **off-protocol forgery**: with the retained trapdoor (or a weak-FS exploit), generate a valid proof for a false statement and show `snarkjs groth16 verify` accepting it. For a vk mismatch, show a proof for the wrong circuit verifying. For FS ordering, show the biased challenge and the resulting accepting proof. Include the verifier output.

## Fix

Destroy toxic waste and use a public ceremony; verify the setup and vk provenance in CI. Deploy only the vk exported from the audited circuit and keep it immutable. Append every commitment before deriving any challenge, use strong domain separation, and hash into the correct field. Use high-entropy randomness for all blinding, never reused or public-seeded.

## Variants and adjacent bugs

- **Retained toxic waste** — a live trapdoor enables universal forgery.
- **vk/circuit mismatch** — a verifier bound to the wrong relation.
- **FS ordering** — a challenge squeezed before a commitment.
- **Wrong challenge field** — reduced mod `p` instead of `q`.
- **Weak blinding** — zero or low-entropy commitment randomness.

## Do not flag

- A ceremony with verified toxic-waste destruction and a bound vk.
- Transcripts that append all commitments before squeezing challenges.
- High-entropy, fresh blinding per commitment.

## Leads vs findings

- An unverified setup or an FS-ordering smell is a **lead**; the forgery is the finding.
- Show an off-protocol forged proof accepted by `snarkjs groth16 verify`.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/zk` — setup, transcript, and verifier model.
- `tooling/zk-circom` — `snarkjs` ceremony and verification-key commands.
- `vulnerabilities/zk-soundness-completeness` — proof/statement binding.
