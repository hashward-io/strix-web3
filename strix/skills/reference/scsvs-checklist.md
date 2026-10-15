---
name: scsvs-checklist
description: SCSVS v2 verification checklist across architecture, design, implementation, and operational controls, with the intent of each category
---

# SCSVS v2 Checklist

The Smart Contract Security Verification Standard (v2, Composable Security) standardizes smart-contract security across the development lifecycle. This file distills its chapters — **General** (G1–G12), **Components** (C1–C9), and **Integrations** (I1–I4) — into an audit checklist grouped by the classic architecture/design/implementation/operational split. Use it to scope a review, as a threat-modeling prompt, and as a coverage score. The standard assigns no severity on purpose; set severity yourself (`analysis/severity_calibration`).

## Architecture

- [ ] **G1 Architecture, design and threat modeling** — system and trust-boundary diagram exists; asset/data flows are mapped; threat actors and their real capabilities are named; the threat model is current.
- [ ] **C1 Token** — token semantics (mintable, burnable, pausable, fee-on-transfer, permit) are declared and match the interface.
- [ ] **C2 Governance** — proposal lifecycle, quorum, timelock, and execution are specified; flash-loan and vote-buying risks considered.
- [ ] **C3 Oracle** — oracle type, decimals, staleness window, and fallback behavior are specified.
- [ ] **C4 Vault** — share accounting, deposit/withdraw symmetry, and rounding direction are specified.
- [ ] **C5 Bridge** — message validation, replay protection, and finality assumptions are specified.
- [ ] **C6 NFT** — metadata handling, royalties, and transfer hooks are specified.
- [ ] **C7 Liquid staking** — exchange-rate accounting, slashing, and withdrawal-queue behavior are specified.
- [ ] **C8 Liquidity pool** — price/oracle source, LP accounting, and the pool invariant are specified.
- [ ] **C9 Uniswap V4 Hook** — hook permission bitmap and callback trust are specified.
- [ ] **I1 Basic / I2 Token / I3 Oracle / I4 Cross-chain** — trust and failure assumptions on every third-party component are documented.
- [ ] The architecture matches what is actually deployed (addresses, proxies, admin, parameters).
- [ ] **Data integrity** — critical data is validated at system boundaries; no unbounded external input enters core logic.

## Design

- [ ] **G2 Policies and procedures** — security policies, roles, and responsibilities are defined and followed.
- [ ] **G3 Upgradeability** — upgrade mechanism (proxy pattern, admin, timelock) is chosen deliberately; storage layout and initializer safety are designed.
- [ ] **G4 Business logic** — the intended economic behavior is written down and matches the code (`analysis/spec-to-code`).
- [ ] **G5 Access control** — every privileged action has a named role; grant/revoke paths are defined.
- [ ] **Access control implementation** — roles are enforced with modifiers/guards, not by naming convention.
- [ ] **Upgrade implementation** — proxies delegate correctly, initializers are protected, and storage layout is compatible.
- [ ] **Components (C*)** — each component's state machine and invariants are designed before implementation.
- [ ] **Integrations (I*)** — integration failure modes (paused token, stale oracle, reorg) are designed for.

## Implementation

- [ ] **G6 Communications** — external calls handle failure and reentrancy; every low-level return value is checked.
- [ ] **G7 Arithmetic** — overflow, underflow, rounding, and precision are handled; checked math or a safe library is used.
- [ ] **G8 Denial of service** — no unbounded loop, revert-on-one-recipient, or griefable external call blocks a critical path.
- [ ] **G9 Blockchain data** — `block.timestamp`/`number`/`blockhash`/`prevrandao` are not trusted as randomness or as an exact clock.
- [ ] **G10 Gas usage and limitations** — gas costs and block limits are respected; no gas-bombing input.
- [ ] **G11 Code clarity** — naming, comments, and structure make intent legible; no unexplained magic numbers.
- [ ] **G12 Test coverage** — unit, integration, fuzz/invariant, and fork tests cover the critical paths (`custom/fizz-invariants`).
- [ ] **Components (C*)** — token/governance/oracle/vault/bridge/NFT/liquid-staking/pool/hook logic is implemented against the design invariants.
- [ ] **Integrations (I*)** — token, oracle, and cross-chain integration are defensive (`reference/weird-erc20`).

## Operational

- [ ] **Deployment** — deploy scripts and migrations are reviewed; initialization cannot be front-run (`analysis/insecure-defaults`).
- [ ] **Key management** — admin/governor/keeper keys use multisig and hardware; no single EOA controls critical funds.
- [ ] **Incident response** — a pause/guardian path exists and is tested; a written response plan is present.
- [ ] **Monitoring** — on-chain alerts for parameter changes, large transfers, and oracle deviations.
- [ ] **Upgrade procedure** — upgrades are timelocked, reviewed, and storage-compatibility-checked.
- [ ] **Dependency and supply chain** — third-party libraries are pinned, reviewed, and tracked.
- [ ] **Disclosure** — audit reports and known issues are published and current.
- [ ] **Compliance score** — a SCSVS coverage report is produced and stored with the repository.

## Sources

- SCSVS (Composable Security): https://github.com/ComposableSecurity/SCSVS
- OWASP ASVS (structural inspiration): https://owasp.org/www-project-application-security-verification-standard/
- Companion skills: `reference/smart-contract-vulnerabilities`, `reference/weird-erc20`, `analysis/spec-to-code`.
