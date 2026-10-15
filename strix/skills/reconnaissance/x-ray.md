---
name: x-ray
description: Pre-audit reconnaissance for a protocol in any ecosystem — architecture, threat model, entry points, invariants, and git history
---

# X-Ray — Pre-Audit Reconnaissance

Generate the pre-audit artifacts before hunting bugs. These are the shared ground every other agent reasons from.

## Step 1 — Enumerate and measure

- Detect the ecosystem, toolchain, and source directory (`reconnaissance/ecosystem-detection`; manifests: `foundry.toml`/`hardhat.config.*`, `Anchor.toml`, `Move.toml`, `Scarb.toml`, CosmWasm `Cargo.toml`, `tact.config.json`, ink! `Cargo.toml`, `Nargo.toml`, `Forc.toml`, NEAR `Cargo.toml`).
- Enumerate in-scope source files for each ecosystem (scope rule excludes deps/builds/tests/interfaces/mocks).
- Record test existence separately from coverage: test files/functions, and whether stateless fuzz, invariant/fuzz tests, formal/symbolic proofs, or fork/real-state tests are present. Coverage command failure does **not** mean tests are absent.
- Run the git security analysis (`reconnaissance/git-history`) for hotspots, dangerous-area changes, and tech debt.

## Step 2 — Read source, classify entry points, synthesize invariants

Read every in-scope file. For each, extract: module/contract/program type and composition/inheritance, roles/access, value-holding state, external calls, fund flows, guard checks (`require`/`assert`/`assert!`/`assert_eq!`/`ensure!`), delta writes (`Δ(var) = +expr`), and one-shot/state transitions.

**Entry-point classification.** From the public/exported/dispatchable function list (exclude view/read-only functions, interfaces, internal library functions, mocks), classify each as:

- **Permissionless** — no modifier and no internal `msg.sender` restriction (verify the body).
- **Role-gated** — has a role modifier, or an internal `if (msg.sender != X) revert`.
- **Admin-only** — `onlyOwner` / `DEFAULT_ADMIN_ROLE` / top-level authority.

For each entry point record: access level, caller type, parameters with trust level (user-controlled / user-signed / keeper / protocol-derived), call chain, state modified, value flow, and reentrancy guard.

`nonReentrant` is not access control. `initializer` is a one-time deploy step — track separately.

**Invariant synthesis.** Walk `analysis/invariant-discovery` and `record_invariant` every verified candidate.

## Step 3 — Write the artifacts

- **`architecture.json` / `x-ray.md`** — overview, scope table (modules by subsystem, nSLOC/lines), actors, trust boundaries, key attack surfaces, protocol-type concerns, test gaps, git history, and a verdict tier (audit-ready / needs work). Vendor-neutral: never reference audit platforms or contest rules.
- **`entry-points.md`** — protocol flow paths (arrow chains) then per-access-level entry-point detail; permissionless entry points get the full block, admin/role-gated may use compact tables when numerous.
- **`invariants.md`** — enforced guards (reference) plus inferred single-contract / cross-contract / economic invariants, each citing its concrete derivation.

## Rules

- **No fabrication.** State "could not determine" when uncertain. Tag spec-derived claims `(per spec)` so readers know what is code-verified vs doc-stated.
- **Verification before claims.** Before asserting a check is missing or bypassable, trace the data flow by reading the code and enumerating the write sites. Subagent summaries are not sufficient.
- For `>20` source files, delegate per-subsystem fact extraction to parallel subagents, then classify entry points from the actual code, not the summaries.
- Group contracts by subsystem in the scope table.
