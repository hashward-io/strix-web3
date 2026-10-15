---
name: governance-attacks
description: Governance and voting — flash-loan voting, quorum, timelock bypass, proposal execution, and delegation bugs
---

# Governance Attacks

Governance is where the protocol's own rules can be turned against it. The attacker is often a token holder with borrowed power.

## Where to look

- **Flash-loan / borrowed voting power.** Power read as `balanceOf` or `getVotes` **at vote time** can be borrowed, used, and repaid in one transaction. Power must be snapshotted (`getPastVotes`) at proposal creation, or the token must be non-transferable/non-borrowable.
- **Quorum manipulation.** A quorum computed from a manipulable `totalSupply` or from a live total; votes counted before/after a supply change.
- **Proposal execution.** An executor that calls arbitrary targets with `delegatecall`; a `timelock` that can be bypassed by a direct call; a proposer/canceler that can be reassigned; a proposal that can be executed twice; a missing `executed` flag.
- **Timelock bypass.** A function with `onlyGovernance` that a role holder can call directly; a `minDelay` that is zero or settable; an emergency path that skips the delay.
- **Delegation.** Self-delegation loops; delegation that does not move voting power atomically; `delegate` to `address(0)` behavior; double-counting a delegated balance.
- **Role-grant via governance.** A governance action that grants a role to an attacker-controlled address, or a `DEFAULT_ADMIN_ROLE` that can self-grant.
- **Voting power transfer.** Transferring tokens after voting but before execution (vote-then-transfer).
- **Malicious proposal data.** A proposal whose calldata differs from its description (reviewer deception) — not on-chain exploitable but a real governance risk; note it.
- **Cross-chain governance.** A message-based vote whose replay or validation is weak (see `vulnerabilities/upgradeability-proxy` and `protocols/bridges-messaging`).

## Attack plan

1. Identify how voting power is measured and **when** it is read relative to the proposal lifecycle.
2. If read at vote time, construct the flash-loan vote.
3. Check quorum source and manipulability.
4. Check the execution path for a bypass, double-execution, or arbitrary-call sink.
5. Check delegated power for double-counting.

## Proof

For flash-loan voting, show the borrow → delegate → vote → execute → repay sequence passing a malicious proposal. For a timelock bypass, show the direct privileged path.

## Fix

Snapshot voting power at proposal creation (`getPastVotes`); fix quorum from a non-manipulable historical total; use OpenZeppelin `TimelockController`; restrict the executor to `self` calls (no arbitrary `delegatecall`); guard against double-execution.
