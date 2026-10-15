---
name: entry-point-analysis
description: Enumerate every externally reachable entry point, classify its access level and parameter trust, and drive audit coverage from the list
---

# Entry-Point Analysis

An audit is only as complete as its list of externally reachable functions. Every bug is reached through an entry point; a miss on this list is a coverage miss, not a missed pattern. Build the list first, then audit from it.

## What counts as an entry point

Enumerate every function, method, or handler an outside actor can invoke. The mechanism differs per ecosystem; the concept does not:

- **EVM** — `public`/`external` functions, `fallback`/`receive`, functions reachable through a proxy's `delegatecall`, anything a dispatcher/router targets, and value force-sent via `selfdestruct`.
- **Solana** — each Anchor instruction handler (`#[program]`), native `process_instruction` match arms, CPI-reachable handlers, and any account a program deserializes.
- **Move** — `public`, `public(friend)` (callable by friends), `entry` (transaction-callable), and Sui `public` entrypoints exposed via `Entry`/`Transfer` wrappers.
- **Cairo** — `#[external(v0)]`/`#[abi(embed_v0)]` functions, the Starknet `__execute__`/`__validate__` entry points, and L1-handler messages.
- **CosmWasm** — `ExecuteMsg`, `QueryMsg`, `MigrateMsg`, `SudoMsg`, and `Reply` arms.
- **TON** — external messages, internal messages routed by opcode, get-methods, and bounced messages.
- **Substrate/ink!** — `#[ink(message)]` dispatchables (read-only vs mutable) and `#[ink(constructor)]`.
- **Sway** — `abi` methods on contracts and predicates; `main` in scripts.
- **NEAR** — `pub fn` methods, `#[init]`, view vs call methods, and promise callbacks.
- **Bitcoin** — Script spend paths, Miniscript policy leaves, and covenant branches.

## Classify each entry point

Record four things for every entry point:

1. **Reachability** — who can call it: anyone, a role, the owner, only another contract, only via a specific router.
2. **Access level** — unguarded, guard-checked (`require`, modifier, `onlyOwner`, `ensure_signed`, capability, `has_one`), or implicitly trusted (hook, callback, CPI callee, keeper).
3. **Parameters** — every argument and its source: `msg.sender`/`caller`, calldata, accounts, remaining accounts, `info.funds`, attached value, L1 message payload, oracle output.
4. **Effect** — what state it writes, what value it moves, which other entry points it can reach.

## Parameter trust

The trust of a parameter, not its type, is where bugs live. For each parameter ask: does the caller control it, does a third party influence it, is it validated, and is that validation checkable inside the callee?

- Caller-controlled address used without an allowlist → arbitrary target (`vulnerabilities/token-integration`, `vulnerabilities/cross-contract-consistency`).
- An account passed into a Solana instruction without an owner/signer check → account confusion.
- A value read from an oracle, another contract, or an L1 message → untrusted until proven.
- A value "known safe" only because one caller is trusted → breaks the moment a second caller exists.

## Drive coverage from the list

1. Sort entry points: unguarded and value-moving first.
2. For each, ask what an unprivileged caller achieves with attacker-chosen parameters. This seeds the FINDING/LEAD list.
3. Cross-check every state variable against the entry points that write it — a critical variable written by an unguarded entry point is a lead.
4. Re-run the list after finding a bug: a missed reachable path is a missed finding.

## Output fields

Add to your notes (and to FINDINGs where relevant):
- `entry_point:` function/handler name and ecosystem.
- `reachability:` anyone | role | contract-only | router-only.
- `trusted_params:` which arguments are validated and by what.
- `unguarded_effects:` the state/value writes on the unguarded path.

## How to apply

Loop a fixed number of passes, and never stop after one:

1. Enumerate entry points from the compiled ABI/dispatcher, not from source comments.
2. Classify access and parameter trust for each; mark the unguarded, value-moving ones red.
3. Audit red entry points first with `hacking_agents/first-principles` and `hacking_agents/execution-trace`; feed every reached sink to `analysis/invariant-discovery`.
4. Every time you discover a new entry point (hook, callback, `fallback`, CPI callee, `Reply` arm), add it and restart the red-marking pass.
5. Stop only when every entry point is classified and every red one has a concrete attacker trace or a located guard (`analysis/counterevidence`).
