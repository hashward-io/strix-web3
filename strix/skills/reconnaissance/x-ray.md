---
name: x-ray
description: Pre-audit reconnaissance for a Solidity protocol — architecture, threat model, entry points, invariants, and git history
---

# X-Ray — Pre-Audit Reconnaissance

Generate the pre-audit artifacts before hunting bugs. These are the shared ground every other agent reasons from.

## Step 1 — Enumerate and measure

- Detect the toolchain and source directory (`foundry.toml`, then `hardhat.config.*`, then `src/`/`contracts/`).
- Enumerate in-scope `.sol` files (scope rule excludes deps/builds/tests/interfaces/mocks).
- Record test existence separately from coverage: test files/functions, and whether stateless fuzz, `foundry_invariant`, `echidna`, `medusa`, `halmos`, `certora`, `fork` tests are present. Coverage command failure does **not** mean tests are absent.
- Run the git security analysis (`reconnaissance/git-history`) for hotspots, dangerous-area changes, and tech debt.

## Step 2 — Read source, classify entry points, synthesize invariants

Read every in-scope file. For each, extract: contract type and inheritance, roles/access, value-holding state, external calls, fund flows, `require`/`assert` guards, delta writes (`Δ(var) = +expr`), and one-shot/state transitions.

**Entry-point classification.** From the `external`/`public` function list (exclude `view`/`pure`, interfaces, internal library functions, mocks), classify each as:

- **Permissionless** — no modifier and no internal `msg.sender` restriction (verify the body).
- **Role-gated** — has a role modifier, or an internal `if (msg.sender != X) revert`.
- **Admin-only** — `onlyOwner` / `DEFAULT_ADMIN_ROLE` / top-level authority.

For each entry point record: access level, caller type, parameters with trust level (user-controlled / user-signed / keeper / protocol-derived), call chain, state modified, value flow, and reentrancy guard.

`nonReentrant` is not access control. `initializer` is a one-time deploy step — track separately.

**Invariant synthesis.** Walk `analysis/invariant-discovery` and `record_invariant` every verified candidate.

## Step 3 — Write the artifacts

- **`architecture.json` / `x-ray.md`** — overview, scope table (contracts by subsystem, nSLOC), actors, trust boundaries, key attack surfaces, protocol-type concerns, test gaps, git history, and a verdict tier (audit-ready / needs work). Vendor-neutral: never reference audit platforms or contest rules.
- **`entry-points.md`** — protocol flow paths (arrow chains) then per-access-level entry-point detail; permissionless entry points get the full block, admin/role-gated may use compact tables when numerous.
- **`invariants.md`** — enforced guards (reference) plus inferred single-contract / cross-contract / economic invariants, each citing its concrete derivation.

## Rules

- **No fabrication.** State "could not determine" when uncertain. Tag spec-derived claims `(per spec)` so readers know what is code-verified vs doc-stated.
- **Verification before claims.** Before asserting a check is missing or bypassable, trace the data flow by reading the code and enumerating the write sites. Subagent summaries are not sufficient.
- For `>20` source files, delegate per-subsystem fact extraction to parallel subagents, then classify entry points from the actual code, not the summaries.
- Group contracts by subsystem in the scope table.
