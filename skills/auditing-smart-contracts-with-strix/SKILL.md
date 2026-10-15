---
name: auditing-smart-contracts-with-strix
description: Audit a Solidity / EVM smart-contract protocol with Strix — an autonomous multi-agent audit that maps the protocol, derives its invariants, runs the specialist attack lenses (reentrancy, access control, oracle/price manipulation, precision and rounding, accounting, upgradeability, signatures, and more), and proves each finding with a Foundry proof-of-concept instead of a static-analysis alert. Runs self-hosted with the open-source CLI against a local Foundry/Hardhat project, a repository, or a deployed contract address. Use when the user asks to audit, security-review, or find vulnerabilities in a smart contract, DeFi protocol, Solidity repo, or on-chain contract.
license: Apache-2.0
metadata:
  author: usestrix
  homepage: https://docs.strix.ai
---

# Auditing smart contracts with Strix

Strix Web3 audits Solidity / EVM code. It reads the source, reasons about value flow and state, and builds a Foundry proof-of-concept for every High/Critical finding.

## When to use

- "Audit this Solidity protocol / Foundry repo / Hardhat project."
- "Find vulnerabilities in this DeFi contract / vault / AMM / lending market."
- "Review this contract at 0x… before we deploy / before mainnet."
- A pre-deployment review, a contest-style audit, or a second opinion on another auditor's findings.

## Prerequisites

- Docker running (the audit runs in a Foundry sandbox container).
- An LLM key: `export STRIX_LLM="openrouter/z-ai/glm-5.3"` and `export LLM_API_KEY="<key>"` (any LiteLLM model id).
- For fork-based PoCs and deployed-contract analysis, an archive RPC endpoint: `export ETH_RPC_URL="https://…"` (or the target chain's).

## Run it (headless)

```bash
# Local Foundry / Hardhat project
strix -n -t ./my-protocol --scan-mode standard --max-budget 20

# A repository
strix -n -t https://github.com/org/protocol --scan-mode deep

# A deployed contract (fetch verified source by address; chain optional)
strix -n -t 1:0x0123456789abcdef0123456789abcdef01234567 --max-budget 20

# Only a change set (PR review)
strix -n -t ./my-protocol --scope-mode diff --diff-base main
```

Scan modes: `quick` (x-ray + core lenses), `standard` (full lens set on the core subsystems), `deep` (exhaustive, default). For a change-set-only review add `--scope-mode diff`.

## Read the results

Artifacts land in `strix_runs/<run-name>/`:

- `audit_report.md` — the assembled report (scope, severity-ranked findings, coverage).
- `vulnerabilities/<id>.md` — one file per finding, with the root cause and the fix.
- `vulnerabilities.json` — machine-readable findings.
- `findings.sarif` — SARIF 2.1.0 for code scanning.
- `run.json` — `status`, targets, and `llm_usage.cost` vs the budget.

Exit codes (headless): `0` no findings, `1` fatal error, `2` findings filed. A `0` only covers what was analyzed — check `coverage` in the report and `run.json` before calling a run clean.

## What it checks

The twelve attack lenses (math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap) across the EVM bug classes: reentrancy, access control, oracle/price manipulation, precision and rounding, accounting and conservation, flash loans, signatures, upgradeability, unchecked returns, ERC-4626 inflation, token integration, DoS/griefing, MEV, governance, and cross-contract consistency.

## Rules

- Audit only code the user is authorized to audit.
- A finding needs a proof: a Foundry PoC or a complete reachable trace. Treat anything less as a lead.
