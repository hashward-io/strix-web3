---
name: property-based-testing
description: Convert the invariant catalog into executable properties and falsify them with the ecosystem's fuzzer — generators, preconditions, shrinking, deterministic PoCs
---

# Property-Based Testing

A fuzzer tests a hypothesis you state; it never tells you what "correct" means. This skill turns the invariant catalog (`analysis/invariant-discovery`) into executable properties and drives the ecosystem's fuzzer to falsify them. A violated property is the strongest automated confirmation that a bug exists; a clean run is bounded evidence, not proof.

## From invariant to property

Every invariant row becomes one property, stated as an assertion over protocol state — not over a single call's return value:

- **Conservation** (`total == Σ parts`) → `assertEq(token.balanceOf(vault), Σ balances)`.
- **Bound** (`withdraw ≤ depositable`) → `assertLe(withdrawn, deposited)` after every sequence.
- **Ratio** (`shares == assets * totalSupply / totalAssets`) → price-per-share monotonicity or exact math.
- **State machine / one-shot** → the latch is never re-armed; terminal states stay terminal.
- **Temporal** → deadline / `lastUpdate` constraints still hold after every call.
- **Cross-contract** → the value the caller assumed still matches the callee's state.
- **Economic** → the derived higher-order statement, citing the invariant IDs it builds on.
- **Guards** — each `require` / `assert` / exact-revert is itself a property the fuzzer can falsify.

If an invariant has no property, record why (not fuzzable, needs external state, unbounded search). An untested invariant is a coverage gap, not a pass.

## Stateless vs stateful

- **Stateless** — one call in isolation: `f(x)` never reverts unexpectedly, output stays in range, rounding favors the protocol. Use the fuzzer's default harness.
- **Stateful** — holds across *any* call sequence; the only kind that catches accounting drift, ordering bugs, and reentrancy. Build a **handler** exposing the protocol's real entry points with bounded actors/amounts, and assert between calls.
- Rank stateful invariants first — that is where the money is.

## Preconditions and assumption accounting

Every property carries hidden assumptions: `totalSupply != 0`, an actor is not the zero address, the token is not fee-on-transfer. Make them explicit as preconditions and count what you excluded — an assumption you cannot state is a bug you cannot see. Separate inputs the attacker controls (arbitrary addresses, amounts, token set, call order) from those the protocol fixes (constants, admin-set parameters).

## Generators that respect real semantics

A property only breaks on *reachable* state, so generators must model the real world:

- **Tokens** — decimals, fee-on-transfer, rebasing, pausable, blacklist, zero-value reverts (`reference/weird-erc20` for EVM). A plain mock token hides every integration bug.
- **Time** — derive from `block.timestamp` / `block.number` / slot, not wall-clock; keep it monotonic where the chain is.
- **Accounts** — distinct actors for user / LP / admin / attacker; the attacker is unprivileged unless the model grants a power (`reconnaissance/threat-modeling`).
- **Bounds** — `bound` / `between` amounts toward meaningful edges (`0`, `1`, `max`, `MIN`, `cap`) rather than uniform noise.
- **Exclusions** — when a real token reverts for a reason unrelated to the bug, exclude it explicitly and record the exclusion.

## Map properties to the ecosystem fuzzer

| Ecosystem | Fuzzer |
|---|---|
| evm | Foundry `forge test` invariant/property tests; Echidna (`tooling/echidna`); Medusa (`tooling/medusa`) |
| solana | `proptest` for unit props; `cargo fuzz`; Trident for stateful instruction sequences |
| move | `sui move test` fuzz inputs; Sui Move Prover for static properties |
| cairo | `snforge test` fuzz tests |
| cosmwasm | `cw-multitest` integration harness |
| substrate | `cargo contract test` / `ink_e2e` |
| sway | `forc test` |
| zk | `nargo test` (Noir); a circuit harness for Circom |
| near | `near-workspaces` sandbox tests |
| bitcoin | `rust-bitcoin` / Miniscript unit tests, `bitcoind -regtest` |

Run more than one tool where available — they explore different paths and break different properties.

## Shrinking and the deterministic PoC

When the fuzzer finds a counterexample, **shrink it**: drop calls, zero amounts, remove actors until the minimal failing sequence remains. Then port that sequence into a deterministic test — explicit call order, hard-coded inputs — in the ecosystem's harness (`custom/poc-construction`). The PoC is the artifact that becomes a finding; the raw fuzzer output is evidence. Assert the *harm* in numbers: drained balance, broken invariant, unauthorized write. Cross-check the bug class against `vulnerabilities/*`.

## Common failure modes

- **Vacuous property** — a precondition that is never satisfiable, so the assertion never runs. The property "passes" because it was never tested.
- **Over-mocked state** — a mock too permissive (no reverts, exact decimals, instant transfers) makes reachable-on-chain bugs unreachable in the harness.
- **Assertion that cannot fail** — a tautology restated as the code's own formula, or an `assert` on a value never written. Re-derive assertions from *intent*, independent of the implementation.
- **Ignored exclusions** — excluding the exact case that fails, or excluding so much the effective domain is trivial.
- **No handler** — a stateful fuzzer without handlers fuzzes the mock, not the code.
- **Green run misread as proof** — record tool, config, `testLimit`, `seqLen`, and which properties had no coverage.

## How to apply

1. Load the catalog and turn each invariant into a property; record the reason for any you cannot.
2. Choose stateless vs stateful per invariant; build handlers and actor/amount/token generators with real semantics.
3. State and count preconditions; separate attacker-controlled from protocol-fixed inputs.
4. Run the ecosystem's fuzzer(s); shrink the first counterexample.
5. Port the shrunk sequence to a deterministic PoC (`custom/poc-construction`); a confirmed break is a finding, a clean run is scoped evidence.
