# 📚 Strix Web3 Skills

## 🎯 Overview

Skills are specialized knowledge packages that give Strix audit agents deep expertise in a specific discipline: a chain/language ecosystem, a bug class, a protocol type, a tool, or a reasoning method. They are the knowledge layer of the Web3 engine — the part that teaches an agent how a senior smart-contract auditor actually works.

This fork audits smart contracts across **EVM, Solana, Move (Sui/Aptos), Cairo/Starknet, CosmWasm, TON, Substrate/ink!, ZK circuits (Circom/Noir), Sway/Fuel, NEAR, Algorand, Cardano (Aiken/Plutus), and Bitcoin Script**.

---

## 🏗️ How skills work

When an agent is created it can load up to **5** skills relevant to its subtask:

```python
create_agent(
    task="Audit the vault's share accounting",
    name="Vault Math",
    skills="hacking_agents/math-precision,protocols/vaults-erc4626,analysis/finding-contract"
)
```

The loaded skills are injected into the agent's system prompt. Skills are addressed either bare (`math-precision`) or qualified by category (`hacking_agents/math-precision`). Every audit starts by detecting the target's ecosystem (`reconnaissance/ecosystem-detection`) and loading the matching `ecosystems/*` playbook.

---

## 📁 Categories

| Category | Purpose |
|----------|---------|
| **`ecosystems/`** | One playbook per chain/language — build, toolchain, bug-class map, proof standard, and fix patterns (`evm`, `solana`, `move`, `cairo`, `cosmwasm`, `ton`, `substrate`, `zk`, `sway`, `near`, `algorand`, `cardano`, `bitcoin`) |
| **`hacking_agents/`** | The twelve specialist attack lenses — each a distinct *method*, not a bug class (math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap). Chain-agnostic. |
| **`vulnerabilities/`** | Bug classes: the EVM set (reentrancy, oracle/price manipulation, precision & rounding, accounting & conservation, flash loans, signatures, upgradeability, unchecked returns, ERC-4626 inflation, token integration, DoS/griefing, MEV, governance, cross-contract consistency, logic flaws) plus per-ecosystem classes (`solana-*`, `move-*`, `cairo-*`, `cosmwasm-*`, `zk-*`, `ton-*`, `substrate-*`, `ink-*`, `sway-*`, `near-*`, `algorand-*`, `cardano-*`, `bitcoin-*`, `stylus-*`) |
| **`protocols/`** | Protocol-type playbooks — AMM/DEX, lending, vaults/ERC-4626, staking/restaking, perps, bridges/messaging, governance, oracles, account abstraction, RWA/tokenization, NFTs/marketplaces, intents/solvers |
| **`tooling/`** | Tool playbooks — Foundry, cast/anvil, Slither, Echidna, Medusa, Halmos, Aderyn, Solidity, Vyper, Python; Anchor/Solana, Move, Cairo/Scarb, CosmWasm, TON, ink!/Substrate, Circom, Noir, Stylus, Sway, NEAR, Algorand, Aiken, Bitcoin Script |
| **`reconnaissance/`** | Pre-audit reconnaissance — ecosystem detection, threat modeling, the x-ray playbook, protocol mapping, and git-history analysis |
| **`reference/`** | Curated external vuln data as checklists — SCSVS, the smart-contract-vulnerabilities taxonomy, Web3Bugs, weirds-ERC20, building-secure-contracts, and per-ecosystem security checklists |
| **`analysis/`** | Internal reasoning skills — finding contract, judging gates, entry points, insecure defaults, sharp edges, spec-to-code, variant/second-opinion/differential review, counterevidence, severity calibration, invariant discovery, property-based testing, fix verification, report language/formatting, senior-auditor mindset |
| **`coordination/`** | Internal orchestration — the root (orchestrator) agent, ecosystem decomposition, the white-box playbook, agent prompts, and dedup/assembly |
| **`scan_modes/`** | Internal scan definitions — quick, standard, deep, and the diff overlay (`--scope-mode diff`) |
| **`custom/`** | Proof construction — the ecosystem-agnostic PoC standard (`poc-construction`), the Foundry PoC builder (`foundry-poc`), and the invariant fuzzing suite (`fizz-invariants`) |

`scan_modes/`, `coordination/`, and `analysis/` are **internal** categories: the engine selects them automatically and they are not offered as user-selectable skills.

---

## 🌐 Ecosystems

| Ecosystem | Languages / frameworks | Bug-class examples |
|---|---|---|
| `evm` | Solidity, Vyper, Yul/Huff, Arbitrum Stylus | reentrancy, oracle/price manipulation, precision, upgradeability |
| `solana` | Rust (Anchor, native, Pinocchio) | missing signer, account validation, PDA seeds, arbitrary CPI, account close/reinit, Token-2022 |
| `move` | Sui Move, Aptos Move | capability misuse, visibility/friend, arithmetic/abort, object & dynamic fields |
| `cairo` | Cairo / Starknet | felt252 math, storage & L1↔L2, access & upgrade, hints/oracles |
| `cosmwasm` | CosmWasm / Cosmos SDK | address canonicalization, message/reply, migration/admin |
| `ton` | FunC, Tact | sender spoofing, bounce handling, cells/gas, jetton trust |
| `substrate` | ink! / Substrate | dispatch origin, storage & weight, ink! ABI/selectors |
| `zk` | Circom, Noir, Halo2, gnark | under-constrained circuits, soundness/completeness, privacy leakage, Fiat–Shamir/setup |
| `sway` | Sway / Fuel | storage & predicates, arithmetic, reentrancy |
| `near` | Rust / AssemblyScript | promise/async trust, predecessor vs signer, storage staking |
| `algorand` | Algorand Python (Puya), PyTeal, Beaker, TEAL | atomic-group composition, rekey/close-remainder drain, inner-txn authorization, box/MBR |
| `cardano` | Aiken, Plutus (V1/V2/V3) | double satisfaction, missing continuation/output checks, datum/redeemer trust, native-token forgery |
| `bitcoin` | Script, Miniscript | covenant soundness, timelocks, sighash flags, malleability |

---

## 🔬 The twelve lenses

The hacking-agents are attack *methods*. The orchestrator spawns one child per lens over the core subsystem set; the lenses deliberately overlap, and the dedup pass reconciles them. They apply to every ecosystem.

- `math-precision` — rounding, precision loss, scale/decimal mixing, unchecked casts and field arithmetic
- `access-control` — permission-model gaps, escalation, broken initialization, authority misuse
- `economic-security` — value flows, token misbehavior, incentive misalignment (unlimited capital assumed)
- `execution-trace` — parameter divergence, value leaks, encoding/ABI mismatch, sentinel bypass
- `invariant` — conservation laws, state couplings, equivalence relationships
- `periphery` — libraries, helpers, encoders, base modules the core trusts
- `first-principles` — unnamed logic bugs; no pattern matching
- `asymmetry` — mismatches between paired functions, branches, and writers/readers
- `boundary` — corner cases at every call site, payable function, and sentinel branch
- `numerical-gap` — bugs at the seam of precision, invariants, and boundaries
- `trust-gap` — bugs at the seam of access control, economics, and asymmetry
- `flow-gap` — bugs at the seam of execution trace, periphery, and protocol intent

---

## 🎨 Writing a skill

A good skill contains:

- **When to use it** — the trigger that makes this skill the right one to load
- **What to look for** — concrete, ecosystem-specific surfaces, not generic advice
- **An attack plan** — the sequence an auditor follows
- **Proof guidance** — what evidence makes a finding confirmed in that ecosystem's harness
- **Fix guidance** — the idiomatic correction
- **YAML frontmatter** — `name` and `description` (used by the loader to list the skill)

Skills add depth. The engine's kill-the-noise discipline lives in `analysis/` — read those before filing anything.

---

> [!NOTE]
> The knowledge here adapts **Pashov Audit Group**'s public Web3 audit methodology (the twelve lenses, the senior-auditor mindset, threat modeling, invariant synthesis, and finding contract), **Trail of Bits**' audit skills (entry-point analysis, insecure defaults, sharp edges, spec-to-code, property-based testing, variant/second-opinion/differential review, and the *building-secure-contracts* development guidelines), and **zkSecurity**'s ZK audit skills, alongside public vuln datasets (SCSVS, kadenzipfel/smart-contract-vulnerabilities, Web3Bugs, weird-erc20) into the Strix engine.
