---
name: slither
description: Slither static analysis — run detectors, triage output, and understand false positives in Solidity audits
---

# Slither

Slither is a fast static analyzer. It finds real bugs and a lot of noise. Its value is as a **lead generator**, not a verdict.

## Running

- `slither .` — analyze the whole project (uses the Foundry/Hardhat build).
- `slither . --exclude-dependencies` — skip `lib/`/`node_modules/`.
- `slither . --filter-paths "test|script|mock"` — restrict to production code.
- `slither . --print human-summary` — contract overview.
- `slither-check-upgradeability old.json new.json` — proxy upgrade storage checks.
- `slither-check-erc <contract> <ERC>` — ERC compliance.
- `slither . --json out.json` — machine-readable output.

## High-signal detectors

- `reentrancy-eth`, `reentrancy-no-eth`, `reentrancy-benign`, `reentrancy-events`.
- `arbitrary-send-eth`, `arbitrary-send-erc20`, `controlled-delegatecall`.
- `uninitialized-state`, `uninitialized-storage`, `uninitialized-local`.
- `suicidal`, `delegatecall-loop`.
- `locked-ether`, `msg-value-loop`, `divide-before-multiply`.
- `missing-zero-check`, `unchecked-transfer`, `low-level-calls`.
- `tx-origin`, `incorrect-equality`, `weak-prng`.
- `shadowing-state`, `unused-return`.

## Triage rules

1. **Reproduce before believing.** For each finding, open the cited location and trace the path. A detector that flags a guarded call is a false positive.
2. **Access-control false positives.** `protected` / `unprotected` are common false positives when a modifier lives on a base contract — check the inheritance.
3. **Reentrancy false positives.** Flagged when state is updated after a call, but the callee is trusted (a known token) or guarded elsewhere — verify the callee.
4. **Severity inflation.** Slither's severity is heuristic; reassign using `analysis/severity_calibration`.
5. **Coverage.** A clean Slither run is not a clean audit; it does not reason about economics, oracle manipulation, live protocol state, or cross-contract intent.

## Workflow

1. `forge build` first so Slither has an up-to-date build.
2. Run with the exclude/filter flags above.
3. Take each finding as a **lead** and investigate the location by hand.
4. Record confirmed findings; record triaged-out leads with the specific control that rules them out.

## Pitfalls

- Slither needs a compiling project; a broken build produces misleading output.
- Downgrade/upgrade to the version compatible with the project's solc.
- Custom `--exclude` patterns can hide real code; review what you filter.
