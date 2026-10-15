<div align="center">

# Strix Web3

### Autonomous AI smart-contract auditor. Multi-agent Solidity / EVM security review with Foundry proof-of-concept exploits.

<br/>

<a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-3b82f6?style=flat-square" alt="License"></a>
<img src="https://img.shields.io/badge/Solidity-EVM-363636?style=flat-square&logo=solidity&logoColor=white" alt="Solidity / EVM">

</div>

> [!NOTE]
> Strix Web3 is a fork of [usestrix/strix](https://github.com/usestrix/strix) re-scoped from general web/application pentesting to **Solidity / EVM smart-contract auditing**. The engine, knowledge base, toolchain, and report format are all Web3: the specialist attack lenses, EVM bug-class skills, a Foundry-first sandbox, and proof-of-concept-driven findings. The managed cloud, HTTP interception proxy, and browser tooling have been removed.

---

## Overview

Strix Web3 runs a team of autonomous audit agents against a Solidity / EVM protocol. They map the code, enumerate the invariants the protocol must hold, run the specialist attack lenses over the core subsystems, and prove every High/Critical finding with a **Foundry proof-of-concept** instead of a static-analysis alert.

**Key capabilities:**

- **Twelve attack lenses** — math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap
- **EVM bug-class knowledge** — reentrancy, access control, oracle/price manipulation, precision & rounding, accounting & conservation, flash loans, signatures, upgradeability, unchecked returns, ERC-4626 inflation, token integration, DoS/griefing, MEV, governance, cross-contract consistency
- **Protocol playbooks** — AMM/DEX, lending, vaults/ERC-4626, staking/restaking, perps, bridges/messaging, governance, oracles
- **Foundry-first sandbox** — forge/cast/anvil, Slither, Aderyn, Echidna, Medusa, Halmos, Node/Hardhat, and a Python venv (`web3`, `eth-abi`)
- **Proof-of-concept driven** — every High/Critical carries a fork test or a complete reachable trace
- **Developer-first output** — severity-ranked findings with an inline, root-cause fix

## Use cases

- **Pre-deployment audit** — review a protocol before it ships.
- **Second opinion / contest prep** — a systematic pass over the code with proof.
- **Fork-based exploit validation** — prove an oracle, price, or accounting bug on live state.
- **CI gate** — a diff-scoped audit on every Solidity pull request.

## 🚀 Quick start

**Prerequisites:**

- Docker (running) — the audit runs in a Foundry sandbox container.
- An LLM API key from any [supported provider](https://docs.strix.ai/llm-providers/overview) (OpenAI, Anthropic, Google, etc.).

```bash
# Install Strix Web3 (same installer as upstream; this fork ships the Web3 engine)
curl -sSL https://strix.ai/install | bash
# ...or run from source: uv run strix --target ./protocol

# Configure your AI provider
export STRIX_LLM="openrouter/z-ai/glm-5.3"
export LLM_API_KEY="your-api-key"

# For fork-based PoCs and deployed-contract analysis
export ETH_RPC_URL="https://your-archive-rpc"

# Audit a local Foundry / Hardhat project
strix --target ./my-protocol
```

> [!NOTE]
> The first run automatically pulls the sandbox Docker image. Results are saved to `strix_runs/<run-name>/`.

## Usage examples

```bash
# Local Solidity project (Foundry or Hardhat)
strix --target ./my-protocol --scan-mode deep

# A repository
strix --target https://github.com/org/protocol

# A deployed contract (verified source fetched by address; chain optional)
strix --target 1:0x0123456789abcdef0123456789abcdef01234567

# A proxy and its implementation together
strix --target ./src --target 0xProxyAddress

# Change-set / PR review
strix --target ./my-protocol --scope-mode diff --diff-base main

# Focus the audit
strix --target ./my-protocol --instruction "Focus on the vault share accounting and oracle staleness"

# Targets from a file, one per non-empty, non-comment line
strix --target-list ./targets.txt
```

Scan modes: `quick`, `standard`, `deep` (default). Add `--scope-mode diff --diff-base <ref>` for change-set reviews. See the [CLI reference](docs/usage/cli.mdx) for every option.

### Headless (CI)

`-n/--non-interactive` runs without the interactive UI. Exits `0` when no findings were filed, `2` when findings exist, `1` on a fatal error.

```bash
strix -n -t ./my-protocol --scan-mode standard --max-budget 20
```

```yaml
name: strix-audit
on:
  pull_request:
    paths: ["**/*.sol", "foundry.toml", "hardhat.config.*"]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - run: curl -sSL https://strix.ai/install | bash
      - env:
          STRIX_LLM: ${{ vars.STRIX_LLM }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          ETH_RPC_URL: ${{ secrets.ETH_RPC_URL }}
        run: strix -n -t . --scope-mode diff --diff-base "origin/${{ github.base_ref }}" --max-budget 15
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with: { sarif_file: strix_runs }
```

## 📄 Results

Every run writes to `strix_runs/<run-name>/`:

- `audit_report.md` — the assembled report (scope, severity-ranked findings, coverage).
- `vulnerabilities/<id>.md` — one file per finding, with root cause and fix.
- `vulnerabilities.json` — machine-readable findings.
- `findings.sarif` — SARIF 2.1.0 for code scanning.
- `run.json` — `status`, targets, and `llm_usage.cost` vs the budget.

A `0` exit only covers what was analyzed — check the report's coverage section and `run.json` before calling a run clean.

## 🖥️ Local web viewer

```bash
strix view                 # open the most recent run
strix view my-run-name     # open a specific run
```

The dashboard shows the findings, a live map of the agent team, and past runs. Nothing leaves your machine; the UI ships prebuilt. It binds to `127.0.0.1` and prints a tokened link.

## 🧠 How an audit is structured

1. **Build** — `forge build` (or `npx hardhat compile`) to get a green tree before trusting any tool.
2. **Recon (x-ray)** — map contracts, roles, value-holding state, entry-point permissions, and external integrations; record the threat model.
3. **Invariants** — enumerate conservation laws, bounds, ratios, state machines, temporal, cross-contract, and economic properties; record each with its write sites.
4. **Lenses** — the twelve specialist lenses over the core subsystems, plus bug-class and protocol specialists.
5. **Prove** — a Foundry PoC or a complete reachable trace for every High/Critical.
6. **Report** — one deduplicated report with an inline fix per finding.

## 🤖 Use Strix Web3 from your coding agent

```bash
npx skills add hashward-io/strix-web3
```

This installs skills for auditing contracts, finding Solidity vulnerabilities, fixing findings, and CI scanning. See [`AGENTS.md`](AGENTS.md) for the quick reference.

## ⚙️ Configuration

```bash
export STRIX_LLM="openrouter/z-ai/glm-5.3"
export LLM_API_KEY="your-api-key"
export ETH_RPC_URL="https://your-archive-rpc"   # optional, for fork PoCs
```

Strix saves your configuration to `~/.strix/cli-config.json`.

### Sign in with a ChatGPT subscription

```bash
strix auth login chatgpt
export STRIX_LLM="chatgpt/gpt-5.4"
strix auth status
```

### Connect your own MCP servers

List servers in `~/.strix/mcp-servers.json` to expose their tools during a run (e.g. an MCP server that provides verified source or block-explorer data). See the [MCP documentation](docs/integrations/mcp.mdx).

## Documentation

In-repo documentation lives under [`docs/`](docs/README.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Layout: `strix/agents` (agent graph + prompts), `strix/tools` (state, reporting, invariants, shell), `strix/runtime` (Docker sandbox), `strix/report` (findings, SARIF), `strix/skills` (internal knowledge pack), `strix/interface` (CLI/TUI/viewer), `containers/` (Foundry sandbox image).

## Acknowledgements

Strix Web3 builds on the open-source work of [Foundry](https://github.com/foundry-rs/foundry), [Slither](https://github.com/crytic/slither), [Echidna](https://github.com/crytic/echidna), [Medusa](https://github.com/crytic/medusa), [Halmos](https://github.com/a16z/halmos), [Aderyn](https://github.com/Cyfrin/aderyn), [LiteLLM](https://github.com/BerriAI/litellm), and [Bubble Tea](https://github.com/charmbracelet/bubbletea), and adapts [Pashov Audit Group](https://github.com/pashov)'s public Web3 audit methodology. Huge thanks to their maintainers.

> [!WARNING]
> **Authorized use only.** Strix Web3 audits the code and contracts you point it at, so only run it against code you own or have **explicit, written permission** to audit. You alone are responsible for obtaining authorization and complying with the law. Strix is provided "as is" with no warranty or liability for misuse.
