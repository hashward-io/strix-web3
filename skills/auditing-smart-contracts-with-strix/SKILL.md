---
name: auditing-smart-contracts-with-strix
description: Audit a smart-contract protocol with Strix on any supported chain — an autonomous multi-agent audit that detects the ecosystem, maps the protocol, derives its invariants, runs the specialist attack lenses, and proves each finding with a runnable proof-of-concept instead of a static-analysis alert. Covers EVM, Solana, Move, Cairo, CosmWasm, TON, Substrate/ink!, ZK circuits, Sway, NEAR, and Bitcoin. Runs self-hosted with the open-source CLI against a local project, a repository, or a deployed on-chain address. Use when the user asks to audit, security-review, or find vulnerabilities in a smart contract, DeFi protocol, or on-chain program.
license: Apache-2.0
metadata:
  author: usestrix
  homepage: https://docs.strix.ai
---

# Auditing smart contracts with Strix

Strix Web3 audits blockchain protocols across every major chain and language. It detects the target's ecosystem, reads the source, reasons about value flow and state, and builds a runnable proof-of-concept for every High/Critical finding.

## When to use

- "Audit this protocol / repo / program." (any chain)
- "Find vulnerabilities in this DeFi contract / vault / AMM / lending market / Solana program / Move package / ZK circuit."
- "Review this contract at 0x… before we deploy / before mainnet."
- A pre-deployment review, a contest-style audit, or a second opinion on another auditor's findings.

## Supported ecosystems

EVM (Solidity, Vyper, Yul/Huff, Arbitrum Stylus), Solana (Anchor/native Rust), Move (Sui, Aptos), Cairo/Starknet, CosmWasm, TON (FunC/Tact), Substrate/ink!, ZK circuits (Circom, Noir, Halo2), Sway/Fuel, NEAR, and Bitcoin Script. The ecosystem is detected automatically from the manifest (Foundry/Hardhat, `Anchor.toml`, `Move.toml`, `Scarb.toml`, `Cargo.toml`, `tact.config.json`, `Forc.toml`, `Nargo.toml`, …).

## Prerequisites

- Docker running (the audit runs in a multi-chain sandbox container).
- An LLM key: `export STRIX_LLM="openrouter/z-ai/glm-5.3"` and `export LLM_API_KEY="<key>"` (any LiteLLM model id).
- For EVM fork-based PoCs and deployed-contract analysis, an archive RPC endpoint: `export ETH_RPC_URL="https://…"`. Other ecosystems use their own local node/validator.

## Run it (headless)

```bash
# Local project — ecosystem detected from the manifest
strix -n -t ./my-protocol --scan-mode standard --max-budget 20

# A repository
strix -n -t https://github.com/org/protocol --scan-mode deep

# A deployed on-chain target (verified source fetched by the agent; chain optional)
strix -n -t 1:0x0123456789abcdef0123456789abcdef01234567 --max-budget 20   # EVM
strix -n -t solana:9xQeWvG816bUx9EPfNqNKpS4Zk5N7gVvDLJq7YvYhq3f             # Solana
strix -n -t sui:0x2                                                        # Sui package

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

The twelve attack lenses (math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap) run chain-agnostically over each ecosystem's own bug classes — the EVM set (reentrancy, access control, oracle/price manipulation, precision and rounding, accounting and conservation, flash loans, signatures, upgradeability, unchecked returns, ERC-4626 inflation, token integration, DoS/griefing, MEV, governance, cross-contract consistency) plus `solana-*`, `move-*`, `cairo-*`, `cosmwasm-*`, `zk-*`, `ton-*`, `substrate-*`, `ink-*`, `sway-*`, `near-*`, `bitcoin-*`, and `stylus-*` classes.

## Rules

- Audit only code the user is authorized to audit.
- A finding needs a proof: a runnable PoC in the ecosystem's harness or a complete reachable trace. Treat anything less as a lead.
