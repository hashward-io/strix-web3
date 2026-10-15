---
name: find-solidity-vulnerabilities-with-strix
description: White-box security review of a Solidity / EVM codebase with Strix — reads the source, traces the actual value and control flow, derives the protocol's invariants, and proves each real issue with a Foundry proof-of-concept in a sandbox fork instead of emitting static-analysis noise. Covers reentrancy, access control, oracle and price manipulation, precision and rounding, accounting and conservation bugs, upgradeability and proxies, signatures and replay, unchecked external calls, ERC-4626 share inflation, token-integration issues, DoS and griefing, MEV, and governance. Use when the user asks to security-review, audit, or find bugs in Solidity source, a Foundry/Hardhat repo, or a smart contract.
license: Apache-2.0
metadata:
  author: usestrix
  homepage: https://docs.strix.ai
---

# Find Solidity vulnerabilities with Strix

A white-box pass over the source. Strix builds the project, maps the protocol, enumerates the invariants that must hold, runs the attack lenses and bug-class specialists, and writes a Foundry PoC for anything High or Critical.

## When to use

- "Review this Solidity repo for bugs."
- "Audit this Foundry / Hardhat project."
- "Is this vault / oracle / lending code safe?"
- A diff review: `--scope-mode diff --diff-base <ref>` scopes the run to the changed `.sol` files.

## Run it

```bash
# Whole project
strix -n -t ./protocol --scan-mode deep --max-budget 20

# Diff / PR review
strix -n -t ./protocol --scope-mode diff --diff-base main

# Focus the audit with instructions
strix -n -t ./protocol --instruction "Focus on the vault share accounting and the oracle staleness checks"
```

## How the review is structured

1. **Build** — `forge build` (or `npx hardhat compile`) to establish a green tree before trusting any tool.
2. **Recon (x-ray)** — map contracts, roles, value-holding state, entry-point permissions, and external integrations; record the threat model.
3. **Invariants** — enumerate conservation laws, bounds, ratios, state machines, temporal, cross-contract, and economic properties; record each with its write sites.
4. **Lenses** — the twelve specialist lenses over the core subsystems, plus bug-class and protocol specialists where the code shape warrants.
5. **Prove** — a Foundry PoC or a complete reachable trace for every High/Critical.
6. **Report** — one deduplicated report with an inline fix per finding.

## Tools used (in the sandbox)

`forge`/`cast`/`anvil`, `slither`, `aderyn`, `echidna`, `medusa`, `halmos`, `solc`, Node/Hardhat, and a Python venv (`web3`, `eth-abi`).

## Read the results

`strix_runs/<run>/`: `audit_report.md`, `vulnerabilities/<id>.md` (root cause + fix), `vulnerabilities.json`, `findings.sarif`, `run.json`.

## Rules

- Only audit code the user owns or is authorized to review.
- Every finding needs proof: a PoC or a complete trace. A scanner hit alone is a lead.
