---
name: second-opinion
description: Adversarially re-review an existing finding or summary — assume it is wrong, try to falsify it, and keep it only if the strongest counterargument fails
---

# Second Opinion

A finding is a claim about the world, and claims deserve an adversary. This pass puts on the opposite hat: assume the finding is wrong and try to falsify it. The goal is not to kill findings — it is to make the survivors credible and to downgrade the ones that cannot survive scrutiny. A finding that has answered its strongest counterargument is worth ten that have not.

## The adversarial mindset

Read the finding as an attacker who wants it to be false, or as the developer who will reply "actually, this is fine because…". Your job is to find the "because". Only a specific, located, code-backed control should refute a finding; speculation never does.

- Assume the guard exists until you have read every path and shown it does not.
- Assume the state is reachable until you have shown a precondition blocks an unprivileged actor.
- Assume the impact is real until you have shown the value cannot reach the attacker.
- Do **not** accept "the admin would not do that", "users would notice", "it is unlikely" as refutation — those **clear** the finding.

## Falsification checklist

Work each item against the finding's own trace:

- **Guard re-check** — read every `require`/`assert`/modifier/`ensure_*`/`has_one`/capability check on the attacker-reachable path. Does one run *before* the sink on *every* branch? If yes → ruled out.
- **Reachability** — can an unprivileged actor reach the vulnerable state in a real deployment, or does it require a privileged setup outside normal operation? Name the actor and the exact calls.
- **Value flow** — does the value actually leave to the attacker, or does it stay in-protocol / go to a third party? Trace the delta, not the intention.
- **Trust assumptions** — does the exploit require the attacker to control a token, oracle, or contract the system explicitly trusts? If the system's threat model excludes it, downgrade.
- **Asymmetry / self-harm** — is the only victim the attacker? An actor who can only hurt themselves is not a finding.
- **Documented tradeoff** — rounding dust, MEV, first-depositor `MINIMUM_LIQUIDITY`, admin-by-design. Flag only if it compounds or zeroes value.
- **Duplicate / already covered** — is this the same root cause as another item? Merge; do not double-count.
- **Proof integrity** — does the PoC actually demonstrate the claimed impact, or a weaker one? Re-run the numbers.

## Verdicts

For each item, assign one of:

- **Confirmed** — the strongest counterargument is located, code-backed, and fails. Keep the finding.
- **Downgraded** — a guard or precondition weakens reachability/impact. Lower severity or convert to a LEAD.
- **Ruled out** — a located control blocks every path. Drop it and record why.
- **Unresolved** — you could not read enough to decide. Keep it as a LEAD with the open question stated; missing information is never proof of safety (`analysis/counterevidence`).

## Common false refutations

Reject these as reasons to drop a finding — they clear it, they do not refute it:

- "The attacker would only hurt themselves." Verify it; if it is truly self-harm, it is a non-finding — but verify, never assume.
- "No one would call it that way." Attackers choose the call.
- "The admin would never do that." If the impact needs an admin, say so and score it as centralization, not as safe.
- "It is only an edge case." Edge cases are where bugs live.
- "The gas cost is too high." Compute it; do not assume.
- "The tests pass." Tests encode the author's assumptions, which may be wrong.

Only a specific, located, code-backed control rejects a finding.

## Confidence after review

Re-set `confidence` honestly:

- `high` — working PoC, or a complete reachable source→control→sink→impact trace.
- `medium` — static-only trace, or a reachable path with an unproven step.
- `low` — plausible but missing a piece; a LEAD.

State what specific evidence would change the verdict — a test, a value, a deployment fact.

## How to apply

1. Pick the highest-severity or most-surprising item first; those carry the most risk of being wrong.
2. Run the falsification checklist item by item; quote the code that decides each.
3. Assign a verdict and rewrite the `counterevidence` field with the strongest surviving argument.
4. Downgrade or drop on a located control; keep and promote otherwise.
5. Repeat on your own fresh findings before filing, and on the assembled summary before it ships (`coordination/dedup-and-assembly`).
