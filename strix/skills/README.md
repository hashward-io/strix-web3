# 📚 Strix Web3 Skills

## 🎯 Overview

Skills are specialized knowledge packages that give Strix audit agents deep expertise in a specific discipline: an EVM bug class, a protocol type, a tool, or a reasoning method. They are the knowledge layer of the Web3 engine — the part that teaches an agent how a senior smart-contract auditor actually works.

This fork audits **Solidity / EVM** protocols only.

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

The loaded skills are injected into the agent's system prompt. Skills are addressed either bare (`math-precision`) or qualified by category (`hacking_agents/math-precision`).

---

## 📁 Categories

| Category | Purpose |
|----------|---------|
| **`hacking_agents/`** | The twelve specialist attack lenses — each a distinct *method*, not a bug class (math-precision, access-control, economic-security, execution-trace, invariant, periphery, first-principles, asymmetry, boundary, numerical-gap, trust-gap, flow-gap) |
| **`vulnerabilities/`** | EVM bug classes — reentrancy, access control, oracle/price manipulation, precision & rounding, accounting & conservation, flash loans, signatures, upgradeability, unchecked returns, ERC-4626 inflation, token integration, DoS/griefing, MEV, governance, cross-contract consistency, logic flaws |
| **`protocols/`** | Protocol-type playbooks — AMM/DEX, lending, vaults/ERC-4626, staking/restaking, perps, bridges/messaging, governance, oracles |
| **`tooling/`** | Tool playbooks — Foundry, cast/anvil, Slither, Echidna, Medusa, Halmos, Aderyn, Solidity language, Python |
| **`reconnaissance/`** | Pre-audit reconnaissance — the x-ray playbook, protocol mapping, and git-history analysis |
| **`analysis/`** | Internal reasoning skills — finding contract, judging gates, counterevidence, severity calibration, invariant discovery, fix verification, report language, report formatting, senior-auditor mindset |
| **`coordination/`** | Internal orchestration — the root (orchestrator) agent, the white-box playbook, agent prompts, and dedup/assembly |
| **`scan_modes/`** | Internal scan definitions — quick, standard, deep, and the diff overlay (`--scope-mode diff`) |
| **`custom/`** | Invariant fuzzing (fizz) and the Foundry proof-of-concept builder |

`scan_modes/`, `coordination/`, and `analysis/` are **internal** categories: the engine selects them automatically and they are not offered as user-selectable skills.

---

## 🔬 The twelve lenses

The hacking-agents are attack *methods*. The orchestrator spawns one child per lens over the core subsystem set; the lenses deliberately overlap, and the dedup pass reconciles them.

- `math-precision` — rounding, precision loss, scale/decimal mixing, unchecked casts
- `access-control` — permission-model gaps, escalation, broken initialization
- `economic-security` — value flows, token misbehavior, incentive misalignment (unlimited capital assumed)
- `execution-trace` — parameter divergence, value leaks, encoding mismatch, sentinel bypass
- `invariant` — conservation laws, state couplings, equivalence relationships
- `periphery` — libraries, helpers, encoders, base contracts the core trusts
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
- **What to look for** — concrete Solidity-specific surfaces, not generic advice
- **An attack plan** — the sequence an auditor follows
- **Proof guidance** — what evidence makes a finding confirmed
- **Fix guidance** — the idiomatic correction
- **YAML frontmatter** — `name` and `description` (used by the loader to list the skill)

Skills add depth. The engine's kill-the-noise discipline lives in `analysis/` — read those before filing anything.

---

> [!NOTE]
> The knowledge here adapts **Pashov Audit Group**'s public Web3 audit methodology (the twelve lenses, the senior-auditor mindset, invariant synthesis, and finding contract) into the Strix engine.
