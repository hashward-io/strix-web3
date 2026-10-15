---
name: zk-privacy-leakage
description: ZK privacy leakage — extra public signals, predictable nonces, leaked intermediates, nullifier linkage, anonymity-set leaks, prover-hint side channels
---

# Zero-Knowledge Leakage

A ZK proof hides the witness, but only the parts the statement does not expose. Every public signal, reused nonce, unblinded commitment, and logging hint is a channel that can de-anonymize the prover or reveal a secret. Privacy bugs are often High even when the circuit is sound.

## Where to look

- **Extra / over-broad public signals.** Every signal in `public` (Circom) or a public input (Noir) is visible to the verifier and on-chain. A private witness accidentally declared public (an amount, an address, a secret) is leaked. Diff the `main` public list against what the dApp must reveal.
- **Derived public signals.** A public signal that is a function of a secret (e.g. publishing a commitment alongside a raw value) re-exposes the secret.
- **Predictable randomness / nonces.** Commitment blinding factors, proof nonces, and nullifiers must be unpredictable. A nonce derived from public data, a constant, or a value reused across proofs links transactions and can reveal the witness.
- **Nonce source in witness generation.** Check the JS/TS/Noir witness-generator for how `r`, `blinding`, and nonces are seeded; a `Math.random` fallback or a fixed seed is a leak.
- **Leaked intermediate values in public inputs.** Commitments must be hiding: `H(value)` with a low-entropy `value` (small amounts, booleans, addresses from a small set) is brute-forceable.
- **Correlating metadata.** Public signals such as leaf index, set size, block number, or timestamp that correlate with the prover narrow the anonymity set.
- **Nullifier linkage.** A nullifier `H(secret, ...)` must (a) be deterministic per secret to prevent double-spend, and (b) not be linkable across contexts. Missing or shared **domain separators** mean the same nullifier recurs in two pools/apps, linking the user.
- **Nullifier exposing the secret.** A nullifier whose preimage is recoverable, or which equals `H(secret)` with no extra entropy, links to any other use of the same secret.
- **Membership / anonymity-set leaks.** In a Merkle-membership proof, leaking the **leaf index**, the set contents, or the tree height reveals who is in the set. Deterministic leaf ordering, sequential indices, and a small/static set shrink anonymity.
- **Reused commitments / rerandomization.** Reusing the same blinding `r` across two commitments to the same value makes them linkable (the difference cancels). Confirm fresh randomness per commitment.
- **Side channels in prover hints.** Unconstrained/brillig hints and witness code can leak: `console.log`/`println` of witness values, `console.error` in Circom witness JS, throwing errors that embed secrets, or timing/memory differences tied to the secret.
- **On-chain event leakage.** Logging the commitment preimage, recipient, or full payload in an event defeats the proof's privacy.

## Attack plan

1. List all public signals/inputs; classify each as necessary or over-broad.
2. For each commitment, check the value space and the blinding factor's source.
3. For each nullifier, verify the domain separator and that it does not expose the secret.
4. Inspect membership proofs for index/ordering/set-size leaks.
5. Read the witness-generator and hint code for logging/error channels.
6. Try to link two proofs from the "same" user by comparing public signals and events.

## Proof

Show the leak concretely: two proofs that can be linked by a shared nullifier/nonce/signal; a public signal that reveals a supposed-secret value; or a brute-force that recovers a low-entropy commitment. A script that correlates public signals across transactions is strong evidence. For a hint channel, show the logged value.

## Fix

Minimize public inputs to exactly the statement. Use fresh, unpredictable randomness for every commitment and check it is not derived from public data. Add explicit domain separators to nullifiers and ensure they never encode the secret. Hide Merkle indices and avoid exposing set metadata. Strip all logging from witness/hint code and never place secrets in error messages or events.

## Variants and adjacent bugs

- **Over-public signals** — a witness value declared public.
- **Predictable nonce** — a blinding factor derived from public data.
- **Nullifier linkage** — a missing domain separator links contexts.
- **Anonymity-set leak** — a leaked leaf index or set metadata.
- **Hint side channel** — witness values logged or placed in errors.

## Do not flag

- Public signals that are exactly what the statement must reveal.
- Commitments with fresh, high-entropy blinding.
- Nullifiers with a correct domain separator that never encode the secret.

## Leads vs findings

- A public signal that *could* leak is a **lead**; the linkage or recovery is the finding.
- Show two linkable proofs, a recovered secret, or a logged witness value.
- Severity is one of **Critical, High, Medium, Low, Informational**.

## Related skills

- `ecosystems/zk` — privacy and commitment model.
- `tooling/zk-noir` — Noir tooling and witness generation.
- `vulnerabilities/zk-setup-and-fiat-shamir` — randomness and setup trust.
