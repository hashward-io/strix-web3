# Strix Web3 — Agent Guide

Strix Web3 is an open-source autonomous AI **smart-contract auditor** for Solidity / EVM. This file is for AI coding agents that want to **use** Strix Web3 (run contract audits) or **contribute** to it.

## Using Strix Web3 from an agent

Install the agent skills for step-by-step workflows:

```bash
npx skills add hashward-io/strix-web3
```

- `auditing-smart-contracts-with-strix` — audit a Solidity/EVM protocol (local project, repo, or deployed address) and read the results
- `find-solidity-vulnerabilities-with-strix` — white-box review of a Solidity codebase
- `fix-solidity-vulnerabilities-with-strix` — remediate findings and re-run Strix to prove each fix
- `ci-smart-contract-scanning-with-strix` — add a diff-scoped contract audit gate to CI/CD

**Run it (self-hosted, free, BYO LLM key, needs Docker):**

```bash
curl -sSL https://strix.ai/install | bash        # install
export STRIX_LLM="openrouter/z-ai/glm-5.3"        # any LiteLLM model id
export LLM_API_KEY="<key>"
export ETH_RPC_URL="<archive-rpc>"                # optional, for fork PoCs
strix -n -t ./protocol --scan-mode standard --max-budget 20   # headless; always use -n
```

- Requires Docker running. Runs take minutes (`quick`) to hours (`deep`) — run in the background.
- Exit codes (headless): `0` no findings, `1` fatal error, `2` findings filed. A `0` only covers what was analyzed — check the report's coverage section and `run.json` (`status`, `llm_usage.cost` vs the budget) before calling a run clean.
- Artifacts in `strix_runs/<run-name>/`: `audit_report.md`, `vulnerabilities/<id>.md`, `vulnerabilities.json`, `findings.sarif` (SARIF 2.1.0), `run.json`.
- Scan modes: `quick`, `standard`, `deep`. Combine with `--scope-mode diff --diff-base <ref>` for a change-set review.
- Targets: a local Solidity project directory, a Git repository URL, or a deployed contract address (`0x<40 hex>`, optionally `chain:0x<40 hex>`).
- Only audit code the user is authorized to audit.

## What the engine checks

The twelve attack lenses (math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap) over the EVM bug classes (reentrancy, access control, oracle/price manipulation, precision/rounding, accounting/conservation, flash loans, signatures, upgradeability, unchecked returns, ERC-4626 inflation, token integration, DoS/griefing, MEV, governance, cross-contract consistency) and protocol playbooks (AMM/DEX, lending, vaults, staking/restaking, perps, bridges/messaging, governance, oracles).

Every High/Critical finding must carry a Foundry proof-of-concept or a complete reachable trace; anything less is a lead.

## Contributing to this repo

- Python 3.12+, managed with `uv`. Install dev deps: `make dev-install`.
- Lint/format/type-check/security, all in one: `make check-all` (ruff, mypy, bandit).
- Tests: `uv run pytest`.
- Run from source: `uv run strix --target <target>`.
- Layout: `strix/agents` (agent graph + prompts), `strix/tools` (state, reporting, invariants, shell), `strix/runtime` (Docker sandbox), `strix/report` (findings, SARIF), `strix/skills` (internal knowledge pack the audit agents load — different from the consumer skills in `skills/`), `strix/interface` (CLI/TUI/viewer), `containers/` (Foundry sandbox image).
- Pre-commit hooks: `make pre-commit` (or `uv run pre-commit install`).
