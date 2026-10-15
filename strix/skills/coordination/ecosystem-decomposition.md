---
name: ecosystem-decomposition
description: How the root agent splits a multi-ecosystem or multi-chain protocol into parallel audit workstreams
---

# Ecosystem Decomposition (Root Agent)

When the target spans more than one chain, language, or subsystem, the root agent's first
job is to split it into independent workstreams — one per ecosystem — and give each its own
specialists. A single "audit everything" child mixes toolchains and produces shallow results.

## Detect, then split

Run `reconnaissance/ecosystem-detection` first (delegate to a recon child). It returns a list
of `(ecosystem, path, build system)` entries. Group the tree by that list.

For each ecosystem, spawn one **ecosystem lead** child carrying:

- the matching `ecosystems/<name>` skill,
- the matching `tooling/<tool>` skill,
- `analysis/invariant-discovery` and `analysis/fix_verification` (whitebox),
- one or two `vulnerabilities/*` skills for the highest-risk classes on that chain.

The ecosystem lead runs recon, builds, synthesizes invariants, and then either audits its
scope directly or spawns lens children scoped to its own ecosystem.

## Then audit the seams

Bridges, cross-chain messaging, shared oracles, wrapped/bridged assets, and L2↔L1 rollups
are where ecosystem boundaries leak. Give the seams their own child with
`protocols/bridges-messaging` plus the two ecosystems it joins. Do not assume one side's
trust assumptions hold on the other.

## Assignment rules

- **One ecosystem per child** — never hand a child two toolchains.
- **No duplicate scope** — before spawning, `view_agent_graph`; each child owns a disjoint
  file set.
- **Same twelve lenses everywhere** — `hacking_agents/*` are chain-agnostic; each ecosystem
  still runs them, but over its own bug-class map.
- **Per-ecosystem proof standard** — tell each child which harness confirms a finding
  (`custom/poc-construction`); a finding without its chain's proof is a lead.
- **Per-ecosystem severity** — a Medium on one chain is not a Medium on another; calibrate
  with `analysis/severity_calibration` against that chain's real loss surface.

## Coverage

Record one coverage row per `(ecosystem, subsystem)` surface, plus rows for the seams. The
final report states which ecosystems were audited, which were only mapped, and which were out
of scope — silence on an ecosystem is a coverage gap, not a clean result.
