---
name: web3bugs-taxonomy
description: Web3Bugs (ICSE'23) taxonomy of real code4rena bugs — functional vs oracle-detected, a checklist, and why most exploits are semantic
---

# Web3Bugs Taxonomy

The Web3Bugs dataset (Zhang et al., ICSE'23, "Demystifying Exploitable Bugs in Smart Contracts") labels real, exploitable bugs from Code4rena contests. Its central finding: a large share of exploitable bugs are **functional bugs** — semantic mistakes that a simple, general oracle (reentrancy, "does the balance go negative", "can a stranger call this") cannot detect. It labels each bug with **O** (out of scope), **L** (detectable with simple/general oracles), or **S** (requires a high-level semantic oracle). Use this taxonomy to remind yourself that the highest-value bugs are usually logic, not pattern hits, and to write function-specific oracles (`custom/fizz-invariants`).

## The two families

- **Oracle-detected (L) bugs** — generic invariants catch them: value conservation, "only the owner can call", "the balance never goes negative", reentrancy. Tools and simple oracles find these.
- **Functional / semantic (S) bugs** — require understanding what the protocol is *supposed to do*: a wrong fee, a mis-scaled amount, a reward that goes to the wrong actor, an update applied to the wrong branch. These need a protocol-specific oracle or a human who read the spec.

The lesson: do not stop when the generic oracles are quiet. Most exploits live in the S class.

## Why functional bugs dominate

- Generic oracles are cheap; semantic oracles require the protocol's intent.
- A functional bug often passes every generic check — balances conserve, access is guarded — while moving value to the wrong actor.
- Attackers specialize in the semantic gap: they read the docs and find the path the author did not test.
- Therefore write a function-specific oracle for every economic promise, not just a conservation check.

## Labels

- **O** — out of scope; excluded from the exploitable set.
- **L** — a simple/general oracle detects it.
- **S** — a high-level semantic oracle is required.

Use the label to decide how to test: L bugs fall to standard invariants; S bugs need a bespoke property (`custom/fizz-invariants`).


## Category checklist

- [ ] **Access control** — a privileged action reachable by the wrong actor, or a public action that should be privileged.
- [ ] **Arithmetic / accounting** — wrong units, missing scale, rounding the wrong way, a fee or share miscomputed.
- [ ] **Oracle / price** — spot vs TWAP, stale price, decimals mismatch, manipulable source.
- [ ] **Reward / distribution** — rewards credited to the wrong set, double-counted, or accrued over the wrong interval.
- [ ] **State update** — a variable updated in one path but not its sibling; stale cache; a missing mirror update.
- [ ] **Token integration** — fee-on-transfer, rebasing, non-standard return, decimals (see `reference/weird-erc20`).
- [ ] **Fee / parameter handling** — a fee applied to the wrong base, a cap ignored, a parameter unvalidated.
- [ ] **Liquidation / health** — an account liquidatable when healthy or vice versa; bad-debt path.
- [ ] **Upgrade / initialization** — uninitialized state, storage layout, front-run init.
- [ ] **Front-running / MEV** — order-dependent outcome, missing slippage/deadline.
- [ ] **Signature / replay** — digest missing domain, nonce, or chain id.
- [ ] **Denial of service** — one actor blocks the many; unbounded iteration.
- [ ] **Cross-contract consistency** — two contracts disagree on shared state.
- [ ] **Token decimals / scaling** — a hardcoded `1e18` against a 6- or 24-decimal token.
- [ ] **Batch / loop accounting** — a per-item value reused across iterations; the last iteration gets a different result.
- [ ] **Time / epoch boundary** — a reward or rate applied across the wrong interval.
- [ ] **Emergency / pause path** — a paused or role-gated path that skips an accounting update.
- [ ] **Migration / initialization** — a value set on deploy that a migration forgets to update.

## How to use it

1. For each category, ask the protocol-specific question: *what does this code promise here, and does it hold on every path?*
2. When you find a functional bug, write the semantic oracle that would have caught it, and add it to the fuzzing suite.
3. Cross-check every "L" finding against the S families — a conservation break is often a disguised functional bug.
4. Treat the classification as a coverage prompt, not a severity scale: an S bug is often Critical precisely because generic tools missed it.

## Sources

- Web3Bugs (ZhangZhuoSJTU), ICSE'23: https://github.com/ZhangZhuoSJTU/Web3Bugs
- Companion skills: `custom/fizz-invariants`, `analysis/spec-to-code`, `analysis/variant-analysis`.
