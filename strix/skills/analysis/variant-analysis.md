---
name: variant-analysis
description: After one bug of a class is found, sweep the codebase, its forks, and its dependencies for every variant of the same root cause
---

# Variant Analysis

A root cause is rarely alone. The same mistaken assumption is usually copied into a sibling function, a fork of the contract, a library the protocol vendored, an older version still deployed, or a test mock that mirrors production. Find one instance of a bug class and your job is not finished — it is just beginning. This pass turns a single finding into coverage of the whole class.

## Abstract the root cause first

Before searching, state the bug as a root cause, not a symptom. Strip contract names, variable names, and the specific value. The abstract form is what you grep for.

- Symptom: `withdraw()` in `VaultV2` credits `amount` after a fee-on-transfer token.
- Root cause: *a transfer result assumed `received == amount`*.
- Variant search: every `transfer`/`transferFrom` followed by crediting the requested amount, in every vault, router, and helper.

Write the root cause as one sentence with the invariant it violates. That sentence is the search key.

## Sweep axes

Search along every axis the root cause can be copied across:

1. **Same file / sibling functions** — the withdraw path was buggy; check deposit, migrate, liquidate, emergency-withdraw.
2. **Inheritance and interfaces** — the base implements it safely, the override does not; or the interface promises a check the implementer skips.
3. **Protocol-internal forks** — `VaultV1`/`VaultV2`, `PoolA`/`PoolB`, `Market`/`IsolatedMarket`.
4. **External forks the code is based on** — the vendored Uniswap/Aave/Compound/OpenZeppelin code and its later patches.
5. **Dependencies and libraries** — `lib/`, `vendor/`, `packages/`, git submodules; the bug may be in the library, not the consumer.
6. **Other deployed versions** — a proxy implementation, an older deployment, a Solana program upgraded from a shared template.
7. **Tests, mocks, and scripts** — a mock that "fixes" the bug hides it in production; a deployment script that sets the vulnerable default.
8. **Cross-ecosystem ports** — the same logic re-implemented on another chain (EVM → Move → Cairo) inherits the same mistake.

## How to search

Search by **name** and by **pattern**, because a copied function may be renamed.

- By name: `transferFrom`, `safeTransferFrom`, `_transfer`, `credit`, `account`, `mint`, `withdraw`, `initialize`, `fuel`, `toUint128`, `as u64`.
- By pattern: every `transfer`/`transferFrom`/`call` followed by a state write of the requested amount; every subtraction before an addition; every `unchecked` block; every `try`/`catch` that continues.
- By invariant: for a conservation bug, list all writers of the two sides of the Δ-pair and check each enforces the invariant.
- Include out-of-scope context (`interfaces/`, `lib/`, `mocks/`, `test/`) when the root cause can live there.

## Escalate each variant

For every candidate:

1. Confirm the same root cause is present (not merely a similar-looking function).
2. Check whether the surrounding guards differ — a variant may be reachable where the original was not, or vice versa.
3. Trace to an impact; a variant that is only reachable by the same trusted role is a weaker duplicate.
4. Report one item per root cause, but list every affected location. A repeat instance is not a new root cause; it is the same bug under `analysis/finding-contract`'s "one vulnerability per item" rule.

## Reporting

- Attribute the class to its first confirmed instance and enumerate all affected sites.
- Cross-reference the sibling findings and note which variant is the strongest-exploitable (the worst variant sets severity).
- If a variant is out of audit scope but likely vulnerable, record it as a lead and name the path.

## How to apply

1. Write the root cause of your latest finding as one sentence.
2. Grep by name and by pattern across in-scope and context files, including forks and dependencies.
3. For each hit, run a mini second-opinion (`analysis/second-opinion`) to confirm or discard it.
4. Enumerate every confirmed site; drive severity from the worst-reachable variant.
5. Repeat for every new finding — a class is only closed when its sweep is empty.
