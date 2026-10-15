---
name: threat-modeling
description: Build the scan's threat model — assets, actors, trust boundaries, privileged powers, external dependencies, and a must-never-happen list that seeds invariants
---

# Threat Modeling

The threat model is the run's shared answer to three questions: what must never be lost, who can reach it, and what assumptions the code places on parties it does not control. Every candidate finding is judged against it, and every invariant in the catalog descends from its "must never happen" list. Derive it before hunting (`reconnaissance/protocol-mapping`), store it with `save_threat_model`, and let agents correct it with `amend_threat_model` as the picture fills in.

## Assets

Name what the protocol exists to protect, and how each can be harmed:

- **Custodied value** — tokens, LP shares, collateral, debt, staked principal.
- **Accounting integrity** — balances, shares, exchange rates, total supply: not stolen but *corrupted*.
- **Authorization state** — ownership, roles, allowlists, admin/ownership.
- **Availability** — a function that must always be callable (withdraw, liquidate, repay).
- **Off-chain effects** — oracle reports, bridge messages, signatures that unlock value elsewhere.

## Actors

For each, record the powers it *really* has, not what the docs claim:

- **Unprivileged user** — calls public functions with arbitrary arguments and value.
- **Privileged role** — admin, owner, governor, keeper, pauser, upgrader.
- **MEV bot / searcher** — mempool ordering, sandwich, backrun, liquidation races.
- **Competitor protocol** — an integration that can act adversarially (a DEX, a lending market).
- **Malicious integration / callback** — a contract the protocol calls that reenters or lies.
- **Compromised admin** — the role is trusted; ask what the worst holder can do and whether a timelock/msig bounds it.
- **Insider / deployer** — front-running initialization, configuring insecure defaults (`analysis/insecure-defaults`).

## Trust boundaries and external dependencies

- **Boundaries** — where privilege changes hands: user→contract, contract→oracle, contract→token, chain→chain, module→module. State which side validates the other.
- **Every external call** — write the assumption placed on the callee (returns a fresh price, honors the transfer, does not reenter, never reverts). An unvalidated assumption is where `vulnerabilities/cross-contract-consistency` lives.
- **Oracles / price feeds** — type (spot/TWAP/Chainlink), decimals, staleness window, fallback, manipulation cost.
- **Tokens** — quirks (`reference/weird-erc20`), fee-on-transfer, rebasing, decimals, pausability.
- **Bridges / messaging** — validation, replay protection, finality, trusted relayer.
- **Upgrades / admin keys** — proxy pattern, storage layout, who can change logic.

## Privileged roles and powers

Enumerate each role and every operational action it can take. For each, note whether a timelock/delay/msig guards the *action* — a transfer delay does not protect against a compromised holder acting instantly.

- mint / burn / pause / unpause; upgrade the implementation or repoint it.
- set fees, caps, oracle addresses, collateral factors, interest models.
- withdraw / sweep stuck funds, rescue tokens, choose `delegatecall` targets.
- grant or revoke roles without a timelock; renounce ownership; migrate storage.

## The "must never happen" list

Write the negative claims the system depends on. They are the seed of `analysis/invariant-discovery`:

- "A user's balance can never decrease without their own action."
- "`Σ user shares` can never exceed `totalSupply`."
- "Shares are never minted for free."
- "An unprivileged account can never move another user's funds or change a privileged parameter."
- "A price used in settlement can never be manipulated within one transaction."
- "A paused path can never execute an exchange."

Convert each line into a positive invariant with a kind and write locations, and `record_invariant` it. A "must never happen" with no property is untested.

## Threat catalog by lens

Run each lens against the assets and boundaries above to seed hypotheses:

- **Access control** — missing/incorrect guard, role escalation, init front-run (`vulnerabilities/access-control`).
- **Economic** — incentive misalignment, flash-loan amplification, first-depositor inflation (`vulnerabilities/flash-loan-attacks`, `vulnerabilities/erc4626-inflation`).
- **Oracle / price** — manipulation, staleness, decimals, single-source trust (`vulnerabilities/oracle-manipulation`).
- **Rounding** — truncation direction, precision loss, repeated-rounding drains (`vulnerabilities/precision-rounding`).
- **Execution / encoding** — ABI/encoding mismatch, `delegatecall`/CPI target confusion, revert/abort semantics (`vulnerabilities/logic-flaws`).
- **Flow** — broken state machine, reentrancy/ordering, value that exits without accounting (`vulnerabilities/reentrancy`, `vulnerabilities/accounting-conservation`).

Chain-specific classes come from `ecosystems/*`; protocol classes come from `protocols/*`.

## Recording and maintaining it

- Store the baseline with `save_threat_model` before subagents start; scope it to the target, not to one slice of the diff.
- Every candidate is judged against it — a "bug" that needs a power the model denies is a **lead**, not a finding.
- When your work contradicts or extends it, call `amend_threat_model` (append-only, attributed); never overwrite the document and drop other agents' corrections.
- Keep it current through `coordination/audit_whitebox` as the code is understood.

## How to apply

1. List assets and how each can be lost or corrupted.
2. List actors with their real powers; add MEV, integration, and compromised-admin stories.
3. Draw the trust boundaries; for every external call/oracle/token, write the assumption placed on it.
4. Enumerate privileged roles and their actions; check each for a timelock that bounds the action.
5. Write the "must never happen" list; convert each line into a recorded invariant (`analysis/invariant-discovery`).
6. Save the model (`save_threat_model`), judge every candidate against it, and amend it as evidence arrives.
