---
name: audit-whitebox
description: White-box orchestration for a source-available Solidity audit — repo mapping, build, invariant catalog, and lens/pass structure
---

# White-Box Audit Playbook

You have the source. The code tells you the boundaries, the entry points, and the invariants before you run anything. Use it.

## Phase 0 — Map and build

1. **Detect the toolchain.** Read `foundry.toml` first if present, then `hardhat.config.*`, then fall back to `src/` or `contracts/`. Record the source directory.
2. **Establish a green build before trusting any tool output.** A static analyzer or fuzzer run against a repo that does not compile produces noise.
   - Foundry: `forge build` (fall back to `forge build --skip test` or `--via-ir`).
   - Hardhat: install deps, then `npx hardhat compile`.
   - If the build fails, treat the failure as a coverage gap: record it and try `forge build --force`, install submodules (`forge install`), or report the exact error verbatim.
3. **Enumerate in-scope files** with the scope rule (source dir minus dependency/build/test/interfaces/mocks). Record the file list with `record_coverage`.

## Phase 1 — Understand before testing

- Map every contract, its inheritance, roles, modifiers, and value-holding state.
- Trace entry points from external/public functions to storage writes and external calls.
- Identify all external integrations (oracles, tokens, other protocols) and their trust assumptions.
- Read for invariants: conservation laws, bounds, ratios, state machines, temporal constraints, cross-contract assumptions.
- Classify protocol type (`protocols/*`) so lens selection is informed.

Delegate this to the x-ray subagent (`reconnaissance/x-ray`) and consume its `x-ray/` artifacts rather than re-deriving them.

## Phase 2 — Invariant catalog

The invariant catalog is the audit's spine. For every property the code must always hold, `record_invariant` it with:

- a **kind** — `conservation`, `bound`, `ratio`, `state_machine`, `temporal`, or `cross_contract`
- a **statement** — the property in one sentence
- **locations** — the `Contract.function` sites that write the constrained state
- whether every write site enforces it (`onchain_enforced`) — the gap is where the bug lives

Use `analysis/invariant-discovery` for the walk and `list_invariants` to track what remains `unproven`.

## Phase 3 — Lens execution

Run the specialist lenses over the core subsystem set. Each child owns one lens and reports what that lens makes visible. Bug-class and protocol skills are loaded per contract where the shape warrants it.

## Phase 4 — PoC and closure

Every candidate ends in exactly one explicit state: `confirmed` (a Foundry PoC, or a complete source→control→sink→impact trace that is reachable), `ruled_out` (you can name the specific control, at a location, that runs on every attacker-reachable path before the sink), or `open_proof_gap` (plausible, unconfirmed, and you could not name such a control). Missing information is never proof of safety — record it as `open_proof_gap`, never as clean.

When source is available, the reporting agent derives the concrete fix inline via `create_vulnerability_report` (`code_locations` with `fix_before`/`fix_after`). Report and fix are one step, not two.
