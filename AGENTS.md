# Strix Web3 — Agent Guide

Strix Web3 is an open-source autonomous AI **smart-contract auditor** for every major chain and language. This file is for AI coding agents that want to **use** Strix Web3 (run contract audits) or **contribute** to it.

## Using Strix Web3 from an agent

Install the agent skills for step-by-step workflows:

```bash
npx skills add hashward-io/strix-web3
```

- `auditing-smart-contracts-with-strix` — audit a smart-contract protocol (local project, repo, or deployed address, any supported chain) and read the results
- `find-solidity-vulnerabilities-with-strix` — white-box review of a Solidity/EVM codebase
- `fix-solidity-vulnerabilities-with-strix` — remediate findings and re-run Strix to prove each fix
- `ci-smart-contract-scanning-with-strix` — add a diff-scoped contract audit gate to CI/CD

**Run it (self-hosted, free, BYO LLM key, needs Docker):**

```bash
curl -sSL https://strix.ai/install | bash        # install
export STRIX_LLM="openrouter/z-ai/glm-5.3"        # any LiteLLM model id
export LLM_API_KEY="<key>"
export ETH_RPC_URL="<archive-rpc>"                # optional, for EVM fork PoCs
strix -n -t ./protocol --scan-mode standard --max-budget 20   # headless; always use -n
```

- Requires Docker running. Runs take minutes (`quick`) to hours (`deep`) — run in the background.
- Exit codes (headless): `0` no findings, `1` fatal error, `2` findings filed. A `0` only covers what was analyzed — check the report's coverage section and `run.json` (`status`, `llm_usage.cost` vs the budget) before calling a run clean.
- Artifacts in `strix_runs/<run-name>/`: `audit_report.md`, `vulnerabilities/<id>.md`, `vulnerabilities.json`, `findings.sarif` (SARIF 2.1.0), `run.json`.
- Scan modes: `quick`, `standard`, `deep`. Combine with `--scope-mode diff --diff-base <ref>` for a change-set review.
- Targets: a local project directory (Foundry/Hardhat, Anchor/Solana, Move, Scarb/Cairo, CosmWasm, Tact/TON, ink!/Substrate, Circom/Noir, Forc/Sway, NEAR, Bitcoin), a Git repository URL, or a deployed on-chain target — EVM `0x<40 hex>`, Solana base58, Sui/Aptos/Starknet `0x<64 hex>` (or short-form with a chain), Cosmos bech32, TON, or Bitcoin — optionally `<chain>:<address>`.
- Only audit code the user is authorized to audit.

## What the engine checks

The target's ecosystem is detected first (`reconnaissance/ecosystem-detection`), then the twelve attack lenses (math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap — chain-agnostic) run over that ecosystem's bug classes. Each ecosystem ships its own playbook (`ecosystems/*`): EVM, Solana, Move (Sui/Aptos), Cairo/Starknet, CosmWasm, TON, Substrate/ink!, ZK circuits (Circom/Noir), Sway/Fuel, NEAR, and Bitcoin Script. Protocol playbooks (AMM/DEX, lending, vaults, staking/restaking, perps, bridges/messaging, governance, oracles, account abstraction, RWA, NFTs, intents) apply across chains.

Every High/Critical finding must carry a runnable proof-of-concept in the ecosystem's harness (or a complete reachable trace); anything less is a lead.

## Contributing to this repo

- Python 3.12+, managed with `uv`. Install dev deps: `make dev-install`.
- Lint/format/type-check/security, all in one: `make check-all` (ruff, mypy, bandit).
- Tests: `uv run pytest`.
- Run from source: `uv run strix --target <target>`.
- Layout: `strix/agents` (agent graph + prompts), `strix/tools` (state, reporting, invariants, shell), `strix/runtime` (Docker sandbox), `strix/report` (findings, SARIF), `strix/skills` (internal knowledge pack the audit agents load — different from the consumer skills in `skills/`), `strix/interface` (CLI/TUI/viewer), `containers/` (multi-chain sandbox image).
- Pre-commit hooks: `make pre-commit` (or `uv run pre-commit install`).
