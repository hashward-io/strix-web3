---
name: logic-flaws
description: Unnamed logic bugs — wrong operators, inverted conditions, wrong variables, missing state updates, and invariant violations with no pattern name
---

# Logic Flaws

The bug that has no name. No standard pattern catches it; you have to read the code and reason about what it is supposed to do.

## How to find them

Read a function and ask, for each line: **what does the code assert here, and is it true?**

- **Wrong operator.** `>=` where `>` is needed (off-by-one at a boundary), `&&` where `||` is needed, `==` where `>=` is needed, `+` where `-` is needed.
- **Inverted condition.** `if (amount > max)` where the intent is `amount <= max`; a `require` that passes on the bad case.
- **Wrong variable.** A function reads `totalDebt` but means `totalCollateral`; copies `from` into `to` and `to` into `from`; uses `msg.sender` where `tx.origin` was intended (or the reverse).
- **Missing state update.** A branch returns early without writing a value a later path expects; an `if` block updates one of two coupled variables.
- **Wrong parameter used twice.** `f(a, b)` computes with `a` twice when it meant `b`.
- **Forgotten require.** A precondition documented in NatSpec but not enforced.
- **Copy-paste bug.** A function duplicated from a sibling with one variable not renamed.
- **Loop bounds.** `i <= length` (off-by-one out of bounds), skipping index 0, or a `break` that stops early.
- **Return value ignored by the caller** (see `vulnerabilities/unchecked-returns`).
- **Semantic mismatch with NatSpec.** The comment says "only once" but nothing enforces it; the comment says "returns the fee" but returns the gross.
- **State machine gaps.** A transition that skips a state, or two transitions that can interleave.

## Method (this is the first-principles lens applied to logic)

1. Pick a function. Write down, in one sentence, what it is supposed to guarantee.
2. Trace the code line by line against that sentence.
3. For each branch, ask what the else case does and whether it was considered.
4. For each write, ask what it must stay consistent with.
5. For each claim in a comment or NatSpec, check it is enforced.
6. Do not pattern-match; a bug you cannot name is still a bug.

## Proof

The proof is the violated guarantee: state the intended property, the input/path that breaks it, and the impact. Even without a known class, a concrete trace that shows the wrong output is a finding.

## Fix

Make the intended guarantee explicit and enforce it; fix the operator/branch/variable; add a `require`; add the missing write; make NatSpec match the code.
