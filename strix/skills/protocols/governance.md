---
name: governance-protocols
description: Governance protocol review — DAO frameworks, timelocks, voting strategies, execution, and treasury control
---

# Governance Protocols

Read governance as a privilege system: who can reach the protocol's most powerful functions, and what stops them.

## Components

- **Token / voting power.** ERC-20/721/1155 with `getVotes`/`getPastVotes`; delegation; checkpoints. Flash-loanable if read live (see `vulnerabilities/governance-attacks`).
- **Governor.** Proposal lifecycle: propose → vote → queue → execute. Quorum, voting period, timelock delay, proposal threshold, cancellation.
- **Timelock.** `minDelay`, `onlyGovernance` on execution, role admin. A zero or settable delay defeats it.
- **Executor / treasury.** A module that can call arbitrary targets; an executor with `delegatecall`; a treasury whose `transfer`/`withdraw` is not governance-gated.
- **Voting strategies.** Pluggable strategies (a plugin that reads an arbitrary balance); a strategy that can be added maliciously; a multi-strategy that double-counts.
- **Upgradeability.** Governance controlling an upgradeable proxy — governance can upgrade to malicious code; note as a trust boundary (see `vulnerabilities/upgradeability-proxy`).

## Where to look

- Every function with an authority check (`onlyGovernance`, `onlyRole`, `onlyOwner`) and whether the authority can be reassigned.
- **Proposal execution sinks.** `execute(targets, values, calldatas)` calling arbitrary contracts — a proposal that calls a malicious target with `delegatecall`, or one that transfers treasury funds.
- **Double execution.** A missing `executed` flag; a proposal that can be queued/executed twice.
- **Quorum manipulation.** A quorum from a live `totalSupply`; a vote that is counted before/after a supply change.
- **Cancellation / guardian.** A guardian that can cancel proposals (censorship) or one that is required to execute (liveness).
- **Timelock bypass.** An `onlyGovernance` function reachable directly; an emergency path skipping the delay.
- **Vote buying / delegation loops.** Self-delegation, delegation to a contract, a delegate that counts twice.

## Attack plan

1. Map the authority graph: which roles reach which sinks.
2. For each sink (treasury, upgrade, param set), find who can reach it and with what delay.
3. Test proposals: pass a malicious one via flash-loaned votes or a quorum flaw.
4. Test execution: double-execution, `delegatecall` sink, timelock bypass.
5. Check cancellation (censorship) and the authority reassignment.

## Proof

For a flash-loan vote, the borrow → vote → execute → repay sequence passing a malicious proposal; for an execution bug, the double-execution or direct privileged call.

## Fix

Snapshot voting power; fix quorum from a historical total; use `TimelockController` with a real delay; restrict executors to self-calls (no arbitrary `delegatecall`); guard double-execution; make role/authority transfer timelocked; document the governance trust boundary.
