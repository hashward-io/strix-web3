---
name: poc-construction
description: The proof standard for a finding in any ecosystem — build a runnable exploit or a complete reachable trace
---

# PoC Construction

A finding is a claim; the proof is what makes it true. Every ecosystem has an idiomatic
harness, but the standard is the same everywhere: **a runnable exploit, or a complete,
reachable source→control→sink→impact trace with no unexplained hop.**

## The proof ladder

1. **Runnable exploit (strongest).** A test that executes the attack and asserts the harm:
   drained funds, broken invariant, unauthorized state change. Prefer a fork/real-state test
   when a deployment exists.
2. **Fuzzer counterexample.** A violated invariant property with the exact input sequence
   found by the fuzzer. Port it into a deterministic test.
3. **Complete trace (weakest acceptable).** If execution is impossible (no build, no fork,
   live-only), trace the path by hand: attacker call → every guard passed → sink → impact,
   citing the exact location of each. A missing hop is not a trace.
4. **Anything less is a LEAD.** A scary function, an analyzer label, or a hunch is a lead,
   not a finding. Leads carry no severity and no fix.

## Anatomy of a runnable PoC

Every PoC states, in order:

- **Setup** — the state the attack needs, made explicit (deploy/fork, seed balances, roles,
  time/block).
- **Attacker** — who calls what, with which privileges (must be unprivileged unless an
  unprivileged amplifier is named).
- **Action** — the exact call sequence, including any malicious helper contract.
- **Assertion** — the measurable harm: `assertGt(attackerAfter - attackerBefore, X)` and
  `assertLt(victimAfter, victimBefore)`. Numbers, not adjectives.
- **Cleanup** — no; a PoC is not production code. Keep it minimal.

## Per-ecosystem harness

| Ecosystem | Harness |
|---|---|
| evm | Foundry test (`forge test`), mainnet fork via `vm.createSelectFork`; see `custom/foundry-poc` |
| solana | LiteSVM or `anchor test` with a local validator; assert lamport/token balances |
| move | `sui move test` / `aptos move test`; or a TS test against a local node |
| cairo | `snforge test` / `starknet-foundry`; assert storage and balances |
| cosmwasm | `cw-multitest` integration test, or a `wasmd` local node |
| ton | `blueprint` + `@ton/sandbox`; assert message flow and balances |
| substrate | `cargo contract test` / `ink_e2e` |
| zk | `nargo execute`/`prove` with a witness that violates soundness; or `snarkjs` verify |
| sway | `forc test` / `fuel-core` local node |
| near | `near-workspaces` sandbox test |
| bitcoin | `bitcoind -regtest` + `bitcoin-cli`, or a `rust-bitcoin`/`miniscript` unit test |

## Rules

- **Fail closed.** If the PoC does not reproduce, the finding is not confirmed — demote it
  or fix the PoC. Never report a bug the harness cannot show.
- **No test-setup artifacts.** A bug that only appears because your mock is unrealistic is
  not a bug. Match real token/account/time semantics.
- **Score only demonstrated impact.** Reachability, a scary name, and a scanner label do not
  set severity; the asserted harm does. See `analysis/severity_calibration`.
- **Attach it inline.** The reporting agent writes the PoC; do not spawn a separate agent to
  re-derive it.
- **Keep it in scope.** The PoC must exercise shipped code, not a modified copy.

## When a runnable PoC is impossible

State the reason explicitly and downgrade confidence (`open_proof_gap`), then give the
strongest complete trace you can. Missing information is never proof of safety.
