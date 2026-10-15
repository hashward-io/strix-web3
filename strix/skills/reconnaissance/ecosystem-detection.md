---
name: ecosystem-detection
description: Detect the chain, language, framework, and build system of a target before auditing — pick the ecosystem and load its playbook
---

# Ecosystem Detection

Strix Web3 audits blockchain protocols across many chains and languages. Before any tool
runs, identify **which ecosystem** the target belongs to, then load that ecosystem's
playbook (`ecosystems/<name>`) and tooling (`tooling/<tool>`). Guessing wrong wastes a whole
pass and can produce findings about code that is not in scope.

## Step 1 — Read the root of the repo

Look for manifest/build files; they identify the ecosystem in one glance.

| Signal | Ecosystem |
|---|---|
| `foundry.toml`, `hardhat.config.*`, `*.sol`, `truffle-config.js`, `brownie-config.yaml` | `evm` |
| `*.vy`, `ape-config.yaml`, `titanoboa` | `evm` (Vyper) |
| `cargo-stylus` / `stylus-sdk` in `Cargo.toml`, `cargo stylus` config | `evm` (Arbitrum Stylus) |
| `Anchor.toml`, `programs/*/src/lib.rs`, `solana-program`/`anchor-lang` in `Cargo.toml` | `solana` |
| `Move.toml`, `sources/*.move`, `sui`/`aptos` in `Move.toml` | `move` |
| `Scarb.toml`, `*.cairo`, `snfoundry.toml` | `cairo` |
| `Cargo.toml` with `cosmwasm-std`, `src/contract.rs`, `schema/` | `cosmwasm` |
| `*.fc`, `*.tact`, `tact.config.json`, `wrappers/` | `ton` |
| `Cargo.toml` with `ink`, `lib.rs` with `#[ink::contract]` | `substrate` |
| `*.circom`, `circom`/`powersoftau`/`snarkjs` in scripts | `zk` (Circom) |
| `Nargo.toml`, `src/main.nr`, `Prover.toml` | `zk` (Noir) |
| `Forc.toml`, `src/main.sw`, `*.sw` | `sway` |
| `Cargo.toml` with `near-sdk`, `src/lib.rs` with `#[near]` | `near` |
| `miniscript`/`bdk`/`bitcoin` crates, `*.miniscript`, ord/runes tooling | `bitcoin` |
| `AlgoKit`/`algokit` config, `algopy`/`pyteal`/`beaker` imports, `*.teal`, ARC-56 `application.json` | `algorand` |
| `aiken.toml`, `validators/*.ak`, `lib/*.ak`, `plutus.json` | `cardano` (Aiken/Plutus) |

Secondary signals: CI workflows, `package.json` scripts, Dockerfiles, and README build
instructions.

## Step 2 — Confirm with a green build

A manifest is a hint; a build is proof. Run the ecosystem's build command (see the
`tooling/*` skill) and record the result.

- A green build is the precondition for every analyzer/fuzzer.
- A red build is a **coverage gap**, not a reason to skip: fix it if possible, otherwise
  record the exact error and continue with source review.

## Step 3 — Handle multi-ecosystem repos

Many protocols are polyglot: an EVM token + a Solana program + a Cosmos module, or a
Cairo app with a Circom circuit. Decompose the repo by ecosystem:

- Split the file tree by extension and manifest.
- Treat each ecosystem as its own subsystem with its own toolchain, proof standard, and
  bug-class map.
- Audit each independently, then audit the **seams** (bridges, message passing, shared
  oracles, wrapped assets) as their own class — see `protocols/bridges-messaging`.

## Step 4 — State the detection result

Record with `record_coverage` (surface = repo root, risk area = "ecosystem detection", outcome =
detected list) and write it into the threat model. Every agent that follows reads it, so the
whole scan attacks the same code in the same language.

## Step 5 — Load the playbook

Once detected, load the matching `ecosystems/<name>` skill (and its `tooling/<name>`), or spawn
a specialist child with it. The ecosystem playbook names the bug classes, the build/test
commands, and the proof standard for that chain. The twelve attack lenses in `hacking_agents/`
apply to **every** ecosystem; the `vulnerabilities/*` skills are ecosystem-specific.

## Rules

- Never audit a target in the wrong language. If a directory is not a supported ecosystem,
  say so once and move on — do not fabricate a toolchain.
- Bytecode-only deployments are a gap: fetch verified source when the explorer supports it,
  otherwise state the limitation and stop short of claiming a finding.
- When a repo mixes ecosystems, never let one ecosystem's findings inflate another's severity.
