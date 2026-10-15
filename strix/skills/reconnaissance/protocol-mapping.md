---
name: protocol-mapping
description: Build the architecture and threat model for a Solidity protocol — contracts, roles, trust boundaries, actors, and value flows
---

# Protocol Mapping

Before testing, build the shared picture of what the protocol is and who the attacker is.

## Architecture

- **Contracts by subsystem** — group by function (core, periphery, vaults, oracles, governance, math libs, deploy scripts). Note inheritance and upgrades.
- **Roles and access** — every role/modifier/`msg.sender` check; who grants what to whom; which powers are instant vs timelocked; which can move user funds.
- **Value-holding state** — mappings and variables that hold balances, collateral, debt, shares, or LP.
- **External integrations** — oracles, tokens, other protocols; the trust and failure assumptions on each.
- **Fund flows** — deposit/withdraw, mint/burn, stake/unstake, borrow/repay, swap; trace value in and out.

## Threat model

Write it once, store it with `save_threat_model`, and let subagents correct it with `amend_threat_model`.

- **Actors** — user, LP, keeper, admin, governance, and any external protocol; each with its real capabilities.
- **Trust boundaries** — where privilege changes hands, and what actually enforces the boundary vs what merely documents it.
- **Attacker capabilities** — what an unprivileged actor controls (arbitrary calls, flash loans, reentrancy, mempool position, arbitrary tokens, arbitrary callbacks).
- **Assets at risk** — the value a successful attack reaches.

## Protocol-type concerns

Classify the protocol (`protocols/*`) and pull in its concerns: AMM/DEX (price manipulation, sandwich, fee accounting), lending (oracle, liquidation, bad debt), vaults/ERC-4626 (share inflation, donation, rounding), staking/restaking (slashing, delegation accounting), perps (funding, liquidation, PnL math), bridges/messaging (replay, message validation, finality), governance (quorum, timelock, proposal execution), oracles (staleness, deviation, decimals, TWAP window).

## Centralization and pause coverage

For each privileged role list every operational action and whether a timelock/msig/delay exists — distinguish role-*transfer* delays from operational-*action* delays; a transfer delay does not protect against a compromised holder acting instantly. Note which critical functions lack a pause. Distribute these into the actors/boundaries/attack-surface sections rather than a standalone "centralization risks" section.
