<div align="center">

# Strix Web3

### Autonomous AI smart-contract auditor. Multi-agent security review for EVM, Solana, Move, Cairo, CosmWasm, TON, Substrate/ink!, ZK circuits, Sway, NEAR, Algorand, Cardano, and Bitcoin — with proof-of-concept exploits.

<br/>

<a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-3b82f6?style=flat-square" alt="License"></a>
<img src="https://img.shields.io/badge/chains-EVM%20%7C%20Solana%20%7C%20Move%20%7C%20Cairo%20%7C%20CosmWasm%20%7C%20TON-363636?style=flat-square" alt="Multi-chain">

</div>

> [!NOTE]
> Strix Web3 is a fork of [usestrix/strix](https://github.com/usestrix/strix) re-scoped from general web/application pentesting to **smart-contract auditing across every major chain and language**. The engine, knowledge base, toolchain, and report format are all Web3: the specialist attack lenses, per-ecosystem bug-class skills, a multi-chain sandbox, and proof-of-concept-driven findings. The managed cloud, HTTP interception proxy, and browser tooling have been removed.

---

## Overview

Strix Web3 runs a team of autonomous audit agents against a blockchain protocol — on any supported chain. They detect the target's ecosystem, map the code, enumerate the invariants the protocol must hold, run the specialist attack lenses over the core subsystems, and prove every High/Critical finding with a **runnable proof-of-concept in that ecosystem's harness** instead of a static-analysis alert.

**Key capabilities:**

- **Multi-ecosystem** — EVM (Solidity, Vyper, Yul/Huff, Arbitrum Stylus), Solana (Anchor/native Rust), Move (Sui, Aptos), Cairo/Starknet, CosmWasm, TON (FunC/Tact), Substrate/ink!, ZK circuits (Circom, Noir, Halo2), Sway/Fuel, NEAR, Algorand (AVM: Algorand Python/PyTeal/Beaker), Cardano (Aiken, Plutus), and Bitcoin Script — with automatic ecosystem detection and per-chain playbooks
- **Twelve attack lenses** — math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap (chain-agnostic)
- **Per-ecosystem bug classes** — the EVM set (reentrancy, oracle/price manipulation, precision & rounding, accounting, flash loans, signatures, upgradeability, unchecked returns, ERC-4626 inflation, token integration, DoS/griefing, MEV, governance, cross-contract consistency) plus `solana-*`, `move-*`, `cairo-*`, `cosmwasm-*`, `zk-*`, `ton-*`, `substrate-*`, `ink-*`, `sway-*`, `near-*`, `algorand-*`, `cardano-*`, `bitcoin-*`, and `stylus-*` classes
- **Protocol playbooks** — AMM/DEX, lending, vaults/ERC-4626, staking/restaking, perps, bridges/messaging, governance, oracles, account abstraction, RWA/tokenization, NFTs/marketplaces, intents/solvers
- **Curated vuln data** — bundled checklists distilled from SCSVS, `smart-contract-vulnerabilities`, Web3Bugs, `weird-erc20`, and per-ecosystem security checklists
- **Multi-chain sandbox** — Foundry/Slither/Aderyn/Echidna/Medusa/Halmos, Anchor/LiteSVM, Sui/Aptos Move + Prover, Scarb/`snforge`, CosmWasm, Circom/`snarkjs`, Noir, Tact/Blueprint, `cargo-contract`, Forc/Fuel, `cargo near`, AlgoKit, Aiken, and Bitcoin Core
- **Proof-of-concept driven** — every High/Critical carries a runnable exploit or a complete reachable trace
- **Developer-first output** — severity-ranked findings with an inline, root-cause fix

## Use cases

- **Pre-deployment audit** — review a protocol before it ships, on any chain.
- **Second opinion / contest prep** — a systematic pass over the code with proof.
- **Fork/real-state exploit validation** — prove a bug against live state (EVM fork, Solana validator, Starknet devnet, and more).
- **CI gate** — a diff-scoped audit on every pull request, in any supported ecosystem.

## 🚀 Quick start

**Prerequisites:**

- Docker (running) — the audit runs in the multi-chain sandbox container.
- An LLM API key from any [supported provider](https://docs.strix.ai/llm-providers/overview) (OpenAI, Anthropic, Google, etc.).

```bash
# Install Strix Web3 — this fork has no release binaries, so run it from source:
git clone https://github.com/hashward-io/strix-web3 && cd strix-web3
make dev-install          # or: uv sync
uv run strix --target ./protocol

# Configure your AI provider
export STRIX_LLM="openrouter/z-ai/glm-5.3"
export LLM_API_KEY="your-api-key"

# For fork-based EVM PoCs and deployed-contract analysis
export ETH_RPC_URL="https://your-archive-rpc"

# Audit a local project (any supported ecosystem)
uv run strix --target ./my-protocol
```

> [!NOTE]
> The sandbox image is not on a public registry yet. `./scripts/docker.sh` builds
> it and tags it `strix-sandbox:dev`, which is the default `STRIX_IMAGE` (see
> [Sandbox Tools](docs/tools/sandbox.mdx)).

## Usage examples

```bash
# Local project — ecosystem detected from the manifest (Foundry/Hardhat,
# Anchor.toml, Move.toml, Scarb.toml, Cargo.toml, tact.config.json, Forc.toml, ...)
strix --target ./my-protocol --scan-mode deep

# A repository
strix --target https://github.com/org/protocol

# A deployed contract — any supported chain (verified source fetched by the agent)
strix --target 1:0x0123456789abcdef0123456789abcdef01234567      # EVM
strix --target solana:9xQeWvG816bUx9EPf...                        # Solana program
strix --target sui:0x2                                                # Sui package
strix --target starknet:0x049d36570d4e46f48e99674bd3fcc84644dd6b8a      # Starknet
strix --target cardano:addr1qy2l9xpjs6z97lztgp3ywp4e8w2q0v6m0c9j0g8x0x3fz2c0j8  # Cardano validator
strix --target algorand:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ  # Algorand app account

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
    paths:
      - "**/*.sol"
      - "**/*.rs"
      - "**/*.move"
      - "**/*.cairo"
      - "**/*.sw"
      - "**/*.circom"
      - "**/*.nr"
      - "foundry.toml"
      - "hardhat.config.*"
      - "Anchor.toml"
      - "Move.toml"
      - "Scarb.toml"
      - "Forc.toml"
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Install Strix (from source)
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          git clone --depth 1 https://github.com/hashward-io/strix-web3 /tmp/strix-web3
          cd /tmp/strix-web3 && uv sync
          /tmp/strix-web3/scripts/docker.sh
          echo "/tmp/strix-web3/.venv/bin" >> "$GITHUB_PATH"
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

1. **Detect** — identify each target's ecosystem, language, and build system (`reconnaissance/ecosystem-detection`); split a multi-chain target into workstreams.
2. **Build** — a green build with the ecosystem's toolchain before trusting any other tool.
3. **Recon (x-ray)** — map modules/contracts/programs/pallets, roles, value-holding state, entry-point permissions, and external integrations; record the threat model.
4. **Invariants** — enumerate conservation laws, bounds, ratios, state machines, temporal, cross-contract, and economic properties; record each with its write sites.
5. **Lenses** — the twelve specialist lenses over the core subsystems, plus per-ecosystem bug-class and protocol specialists.
6. **Prove** — a runnable PoC (in the ecosystem's harness) or a complete reachable trace for every High/Critical.
7. **Report** — one deduplicated report with an inline fix per finding.

## 🤖 Use Strix Web3 from your coding agent

```bash
npx skills add hashward-io/strix-web3
```

This installs skills for auditing smart contracts, finding vulnerabilities, fixing findings, and CI scanning. See [`AGENTS.md`](AGENTS.md) for the quick reference.

## ⚙️ Configuration

```bash
export STRIX_LLM="openrouter/z-ai/glm-5.3"
export LLM_API_KEY="your-api-key"
export ETH_RPC_URL="https://your-archive-rpc"   # optional, for EVM fork PoCs
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

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Layout: `strix/agents` (agent graph + prompts), `strix/tools` (state, reporting, invariants, shell), `strix/runtime` (Docker sandbox), `strix/report` (findings, SARIF), `strix/skills` (internal knowledge pack), `strix/interface` (CLI/TUI/viewer), `containers/` (multi-chain sandbox image).

## Acknowledgements

Strix Web3 builds on the open-source work of [Foundry](https://github.com/foundry-rs/foundry), [Slither](https://github.com/crytic/slither), [Echidna](https://github.com/crytic/echidna), [Medusa](https://github.com/crytic/medusa), [Halmos](https://github.com/a16z/halmos), [Aderyn](https://github.com/Cyfrin/aderyn), [Anchor](https://github.com/coral-xyz/anchor), [Sui](https://github.com/MystenLabs/sui), [Aptos](https://github.com/aptos-labs/aptos-core), [Starknet Foundry](https://github.com/foundry-rs/starknet-foundry), [Scarb](https://github.com/software-mansion/scarb), [CosmWasm](https://github.com/CosmWasm/cosmwasm), [circom](https://github.com/iden3/circom) and [snarkjs](https://github.com/iden3/snarkjs), [Noir](https://github.com/noir-lang/noir), [Tact](https://github.com/tact-lang/tact), [ink!](https://github.com/use-ink/ink), [Sway](https://github.com/FuelLabs/sway), [near-sdk](https://github.com/near/near-sdk-rs), [AlgoKit](https://github.com/algorandfoundation/algokit-cli), [Aiken](https://github.com/aiken-lang/aiken), and [rust-miniscript](https://github.com/rust-bitcoin/rust-miniscript), [LiteLLM](https://github.com/BerriAI/litellm), and [Bubble Tea](https://github.com/charmbracelet/bubbletea). It adapts [Pashov Audit Group](https://github.com/pashov)'s public Web3 audit methodology, [Trail of Bits](https://github.com/trailofbits/skills)' audit skills, and [zkSecurity](https://github.com/zksecurity/zk-skills)' ZK skills. Huge thanks to their maintainers.

> [!WARNING]
> **Authorized use only.** Strix Web3 audits the code and contracts you point it at, so only run it against code you own or have **explicit, written permission** to audit. You alone are responsible for obtaining authorization and complying with the law. Strix is provided "as is" with no warranty or liability for misuse.
