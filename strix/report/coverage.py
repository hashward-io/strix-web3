"""``coverage.json`` — the negative space of a scan, with provenance.

A findings list answers "what is wrong". It cannot answer "what did you
check", and in a compliance context that second question is the one that
decides whether a clean result means anything: an auditor reading zero SQL
injection findings cannot tell "tested fourteen endpoints, all parameterized"
apart from "never looked".

This module assembles the artifact that answers it. Two kinds of statement go
in, and they are kept apart on purpose:

- ``agent_reported`` — the coverage ledger (:mod:`strix.tools.coverage.tools`).
  Rich and specific, but it is an agent's account of its own work.
- ``machine_observed`` — facts the runtime recorded regardless of what any
  agent claimed: which agents ran and how they terminated, which skills they
  carried, how many findings were filed, whether the run finished or was cut
  short.

A coverage claim is an attestation, so conflating the two would be the worst
possible failure: a hallucinated "tested and clean" is strictly less honest
than no coverage record at all. Every entry therefore carries its ``source``,
and machine-observed facts contradict rather than confirm — an agent that
carried the ``reentrancy`` skill and recorded nothing about reentrancy
shows up under ``gaps``, and a run that hit its budget ceiling is stamped
``complete: false`` no matter how tidy the ledger looks.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from strix.report.writer import atomic_write_text
from strix.skills import get_available_skills


if TYPE_CHECKING:
    from pathlib import Path


logger = logging.getLogger(__name__)

COVERAGE_FILENAME = "coverage.json"
COVERAGE_SCHEMA_VERSION = 1

#: Ledger outcomes rendered for a reader who has never seen our enum.
OUTCOME_LABELS: dict[str, str] = {
    "reported": "Finding reported",
    "no_issue_found": "No issue identified",
    "ruled_out": "Ruled out",
    "not_applicable": "Not applicable",
    "needs_follow_up": "Requires further review",
}

#: Statuses that mean the agent stopped early rather than finishing its task.
_INCOMPLETE_AGENT_STATUSES = frozenset({"crashed", "stopped", "running", "waiting"})

#: Run statuses that mean the scan itself did not run to completion.
_INCOMPLETE_RUN_STATUSES = frozenset({"failed", "interrupted", "stopped", "running"})

#: Only this skill category names a vulnerability class. ``tooling`` and
#: ``reconnaissance`` skills describe how an agent works, not what it hunts,
#: so holding one implies no coverage obligation.
_RISK_SKILL_CATEGORY = "vulnerabilities"

#: How each vulnerability skill can legitimately appear in a ledger row.
#:
#: Matching a skill to a row is textual, and a skill's filename is not how a
#: auditor writes the class down: an agent carrying ``oracle-manipulation``
#: records "oracle price manipulation", and one carrying ``erc4626-inflation``
#: records "first-depositor share inflation". A row matches when it contains
#: every word of *any one* phrasing here. Skills absent from this map fall back
#: to their own words, so a new skill is merely matched strictly, never crashed
#: on — but add an entry, because a false gap asserts something untrue in a
#: report.
_SKILL_PHRASINGS: dict[str, tuple[str, ...]] = {
    "access-control": (
        "access control",
        "authorization",
        "privilege escalation",
        "permission",
        "ownership",
        "missing modifier",
    ),
    "accounting-conservation": (
        "accounting",
        "conservation",
        "solvency",
        "insolvency",
        "share accounting",
        "balance invariant",
    ),
    "cross-contract-consistency": (
        "cross contract",
        "consistency",
        "integration mismatch",
        "assumption mismatch",
    ),
    "dos-griefing": (
        "denial of service",
        "dos",
        "griefing",
        "unbounded loop",
        "blocked withdrawal",
    ),
    "erc4626-inflation": (
        "erc4626",
        "inflation",
        "share inflation",
        "first depositor",
        "donation attack",
    ),
    "flash-loan-attacks": (
        "flash loan",
        "flashloan",
        "uncollateralized",
        "atomic capital",
    ),
    "governance-attacks": (
        "governance",
        "voting",
        "proposal",
        "quorum",
        "timelock",
    ),
    "logic-flaws": (
        "logic flaw",
        "business logic",
        "state machine",
        "logic error",
    ),
    "mev-frontrunning": (
        "mev",
        "frontrunning",
        "front run",
        "sandwich",
        "backrun",
    ),
    "oracle-manipulation": (
        "oracle",
        "price feed",
        "twap",
        "stale price",
        "chainlink",
    ),
    "precision-rounding": (
        "precision",
        "rounding",
        "truncation",
        "fixed point",
        "integer division",
        "scaling",
    ),
    "price-manipulation": (
        "price manipulation",
        "spot price",
        "price oracle",
        "amm price",
    ),
    "reentrancy": (
        "reentrancy",
        "reentrant",
        "callback",
        "checks effects interactions",
    ),
    "signature-replay": (
        "signature",
        "replay",
        "ecrecover",
        "permit",
        "nonce",
        "eip 712",
    ),
    "token-integration": (
        "token integration",
        "fee on transfer",
        "rebasing",
        "nonstandard erc20",
        "weird erc20",
        "double entry point",
    ),
    "unchecked-returns": (
        "unchecked return",
        "unchecked call",
        "return value",
        "low level call",
        "silent failure",
    ),
    "upgradeability-proxy": (
        "upgradeability",
        "proxy",
        "initializer",
        "storage collision",
        "implementation",
        "delegatecall",
    ),
    # --- Non-EVM ecosystems -------------------------------------------------
    "solana-signer-authorization": (
        "signer",
        "is signer",
        "authorization",
        "missing signer",
        "signer check",
    ),
    "solana-account-validation": (
        "account validation",
        "owner check",
        "type cosplay",
        "account confusion",
        "duplicate mutable",
        "sysvar",
    ),
    "solana-pda-seeds": (
        "pda",
        "seeds",
        "bump",
        "program derived address",
        "seed collision",
    ),
    "solana-cpi-safety": (
        "cpi",
        "cross program invocation",
        "arbitrary program",
        "invoke signed",
    ),
    "solana-close-and-reinit": (
        "close account",
        "account revival",
        "reinitialize",
        "rent",
        "reinit",
    ),
    "solana-token2022": (
        "token 2022",
        "token-2022",
        "transfer hook",
        "transfer fee",
        "permanent delegate",
        "confidential transfer",
    ),
    "solana-arithmetic-and-casts": (
        "checked arithmetic",
        "overflow",
        "cast",
        "truncation",
        "lamport",
        "rounding",
    ),
    "solana-defi-accounting": (
        "amm invariant",
        "reserve",
        "liquidation",
        "share inflation",
        "price feed",
        "accounting",
    ),
    "move-capability-misuse": (
        "capability",
        "witness",
        "authority",
        "publisher",
        "admin capability",
    ),
    "move-visibility-and-friends": (
        "visibility",
        "friend",
        "public package",
        "entry",
        "upgrade policy",
    ),
    "move-arithmetic-and-abort": (
        "move arithmetic",
        "abort",
        "overflow",
        "assert",
        "division",
        "rounding",
    ),
    "move-object-and-dynamic-fields": (
        "shared object",
        "dynamic field",
        "object ownership",
        "table",
        "uid",
        "contention",
    ),
    "cairo-felt-and-math": (
        "felt252",
        "field arithmetic",
        "overflow",
        "u256",
        "rounding",
        "cairo math",
    ),
    "cairo-storage-and-l1-l2": (
        "storage address",
        "storage collision",
        "legacy map",
        "l1 handler",
        "l1 l2",
        "class hash",
    ),
    "cairo-access-and-upgrade": (
        "cairo access control",
        "owner",
        "upgrade",
        "replace class",
        "initializer",
    ),
    "cairo-hints-and-oracles": (
        "hint",
        "oracle",
        "pragma",
        "syscall",
        "timestamp",
    ),
    "cosmwasm-address-and-funds": (
        "address canonicalization",
        "bech32",
        "addr validate",
        "funds",
        "uint128",
        "cw20",
    ),
    "cosmwasm-message-and-reply": (
        "submessage",
        "reply",
        "sudo",
        "unbounded iteration",
        "wasm msg",
    ),
    "cosmwasm-migration-and-admin": (
        "migrate",
        "admin",
        "cw2",
        "ibc",
        "instantiate",
    ),
    "zk-underconstrained-circuit": (
        "under constrained",
        "unconstrained",
        "missing constraint",
        "range check",
        "circom",
    ),
    "zk-soundness-completeness": (
        "soundness",
        "completeness",
        "malleable proof",
        "witness",
        "forged proof",
    ),
    "zk-privacy-leakage": (
        "privacy",
        "zero knowledge",
        "nullifier",
        "anonymity",
        "leak",
    ),
    "zk-setup-and-fiat-shamir": (
        "trusted setup",
        "toxic waste",
        "fiat shamir",
        "transcript",
        "commitment",
    ),
    "zk-noir-specific": (
        "noir",
        "unconstrained",
        "field overflow",
        "brillig",
        "nargo",
    ),
    "ton-sender-and-bounce": (
        "sender address",
        "bounce",
        "external message",
        "ton sender",
        "replay",
    ),
    "ton-cell-and-gas": (
        "cell",
        "gas",
        "dictionary",
        "send raw message",
        "storage rent",
    ),
    "ton-jetton-and-getmethods": (
        "jetton",
        "transfer notification",
        "get method",
        "query id",
    ),
    "substrate-dispatch-origin": (
        "dispatch origin",
        "ensure signed",
        "ensure root",
        "origin",
        "dispatchable",
    ),
    "substrate-storage-and-weight": (
        "storage layout",
        "weight",
        "storage vec",
        "unbounded iteration",
        "set code hash",
    ),
    "ink-storage-and-abi": (
        "abi selector",
        "constructor",
        "cross contract call",
        "reentrancy",
        "ink",
    ),
    "sway-storage-and-predicates": (
        "predicate",
        "storage map",
        "storage slot",
        "sway storage",
    ),
    "sway-arithmetic-and-reentrancy": (
        "sway arithmetic",
        "overflow",
        "asset id",
        "msg sender",
        "reentrancy",
    ),
    "near-promise-and-storage": (
        "promise",
        "async",
        "storage deposit",
        "callback",
        "unbounded iteration",
    ),
    "near-access-and-math": (
        "predecessor",
        "signer account",
        "access key",
        "yocto",
        "overflow",
    ),
    "bitcoin-script-covenants": (
        "covenant",
        "miniscript",
        "script",
        "timelock",
        "sighash",
        "malleability",
    ),
    "stylus-arbitrum-specific": (
        "stylus",
        "wasm",
        "sol storage",
        "delegate call",
        "entrypoint",
    ),
    "algorand-group-transactions": (
        "atomic group",
        "group transaction",
        "gtxn",
        "fee pooling",
        "group index",
    ),
    "algorand-account-and-rekey": (
        "rekey",
        "close remainder",
        "sender",
        "clawback",
        "asset allowlist",
    ),
    "algorand-inner-and-storage": (
        "inner transaction",
        "itxn",
        "caller app",
        "box",
        "minimum balance",
        "app call depth",
    ),
    "cardano-eutxo-double-satisfaction": (
        "double satisfaction",
        "eutxo",
        "continuation",
        "continuing output",
        "unspent output",
    ),
    "cardano-datum-redeemer-context": (
        "datum",
        "redeemer",
        "script context",
        "validity range",
        "signatories",
        "purpose",
    ),
    "cardano-value-and-minting": (
        "minting policy",
        "native token",
        "counterfeit",
        "lovelace",
        "one-shot",
        "value normalization",
    ),
}


def read_agent_graph(state_dir: Path) -> dict[str, Any]:
    """Load the coordinator's snapshot, or ``{}`` when it isn't readable.

    The snapshot is the runtime's own record of the agent tree, written on
    every graph mutation. Reading it here (rather than holding a coordinator
    reference) keeps artifact assembly usable from a finished or resumed run,
    where the live coordinator is gone but the file is still on disk.
    """
    path = state_dir / "agents.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("agent graph snapshot at %s is unreadable", path, exc_info=True)
        return {}
    return data if isinstance(data, dict) else {}


def _normalized(text: str) -> str:
    """Lowercase *text* with punctuation flattened to spaces, for matching."""
    return "".join(char if char.isalnum() else " " for char in text.lower())


def _skill_leaf(skill: str) -> str:
    return skill.rsplit("/", maxsplit=1)[-1].strip().lower()


def _risk_skill_names() -> frozenset[str]:
    """Bare names of every skill that denotes a vulnerability class."""
    try:
        entries = get_available_skills().get(_RISK_SKILL_CATEGORY, [])
        return frozenset(entry["name"] for entry in entries if entry.get("name"))
    except OSError:
        logger.warning("could not enumerate skills for coverage gaps", exc_info=True)
        return frozenset()


def agents_from_graph(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten the coordinator snapshot into one record per agent."""
    statuses = graph.get("statuses")
    if not isinstance(statuses, dict):
        return []
    raw_names = graph.get("names")
    names: dict[str, Any] = raw_names if isinstance(raw_names, dict) else {}
    raw_metadata = graph.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_parents = graph.get("parent_of")
    parents: dict[str, Any] = raw_parents if isinstance(raw_parents, dict) else {}
    # Only an unambiguous root earns the exemption below. A snapshot with no
    # parent links at all makes every agent look parentless, and excusing all
    # of them would silently delete the silent-agent check.
    parentless = [agent_id for agent_id in statuses if not parents.get(agent_id)]
    root_id = parentless[0] if len(parentless) == 1 else None

    agents: list[dict[str, Any]] = []
    for agent_id, status in statuses.items():
        raw_meta = metadata.get(agent_id)
        meta: dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}
        raw_skills = meta.get("skills")
        skills: list[Any] = raw_skills if isinstance(raw_skills, list) else []
        agents.append(
            {
                "agent_id": agent_id,
                "agent_name": names.get(agent_id) or agent_id,
                "status": str(status),
                "skills": [str(skill) for skill in skills],
                "task": str(meta.get("task") or ""),
                "is_root": agent_id == root_id,
            }
        )
    agents.sort(key=lambda agent: str(agent["agent_name"]))
    return agents


def _skill_phrasings(skill: str) -> list[list[str]]:
    """Word lists that would each count as a ledger row naming *skill*."""
    phrasings = _SKILL_PHRASINGS.get(skill) or (skill,)
    return [terms for phrase in phrasings if (terms := _normalized(phrase).split())]


def _entry_is_about(entry: dict[str, Any], phrasings: list[list[str]]) -> bool:
    """True when a ledger row plausibly concerns any phrasing of a risk class."""
    haystack = _normalized(f"{entry.get('risk_area', '')} {entry.get('surface', '')}")
    return any(all(term in haystack for term in terms) for terms in phrasings)


def skill_coverage_gaps(
    entries: list[dict[str, Any]], agents: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Vulnerability classes an agent was equipped for but never recorded.

    A skill assigned to an agent is a declaration of intent that the runtime
    observed independently of anything the agent later said. When no ledger
    row mentions that class, the class is unaccounted for — which is a very
    different report line from "tested, nothing found".
    """
    risk_skills = _risk_skill_names()
    if not risk_skills:
        return []

    carriers: dict[str, list[str]] = {}
    for agent in agents:
        for skill in agent["skills"]:
            leaf = _skill_leaf(skill)
            if leaf in risk_skills:
                carriers.setdefault(leaf, []).append(str(agent["agent_name"]))

    gaps: list[dict[str, Any]] = []
    for skill, agent_names in sorted(carriers.items()):
        phrasings = _skill_phrasings(skill)
        if any(_entry_is_about(entry, phrasings) for entry in entries):
            continue
        gaps.append(
            {
                "kind": "unrecorded_risk_class",
                "risk_area": skill.replace("_", " "),
                "detail": (
                    f"Agent(s) {', '.join(sorted(set(agent_names)))} were assigned the "
                    f"'{skill}' skill, but no coverage entry records this class being "
                    "assessed. Treat it as unexamined, not as clean."
                ),
            }
        )
    return gaps


def _silent_agent_gaps(
    entries: list[dict[str, Any]], agents: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Agents that ran and recorded nothing at all.

    The root agent is exempt while it has children: it delegates and
    reconciles rather than testing, so flagging it on every clean scan would
    put a permanent false line in the report and teach readers to skip the
    section. A root that ran alone tested alone, and is held to the rule.
    """
    recorded_ids = {str(entry.get("agent_id")) for entry in entries if entry.get("agent_id")}
    delegated = len(agents) > 1
    gaps: list[dict[str, Any]] = []
    for agent in agents:
        if agent["agent_id"] in recorded_ids or (agent["is_root"] and delegated):
            continue
        gaps.append(
            {
                "kind": "agent_recorded_no_coverage",
                "agent_name": agent["agent_name"],
                "detail": (
                    f"{agent['agent_name']} ran (status: {agent['status']}) without "
                    "recording any coverage. Whatever it examined is absent from this "
                    "record."
                ),
            }
        )
    return gaps


def _unresolved_gaps(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ledger rows the agents themselves left open."""
    return [
        {
            "kind": "needs_follow_up",
            "surface": entry.get("surface", ""),
            "risk_area": entry.get("risk_area", ""),
            "detail": str(entry.get("evidence") or "Left open without a stated reason."),
        }
        for entry in entries
        if entry.get("outcome") == "needs_follow_up"
    ]


def _completeness(
    run_record: dict[str, Any],
    agents: list[dict[str, Any]],
    exit_reason: str | None,
) -> dict[str, Any]:
    """Whether this record can be read as a complete account of the scan.

    Any of these makes it partial, and the caveats say which: the run did not
    reach ``completed``, an agent was still live or died when the scan ended,
    or the run stopped for a reason other than the root agent deciding it was
    done (budget ceilings are the common case).
    """
    status = str(run_record.get("status") or "unknown")
    caveats: list[str] = []

    if status in _INCOMPLETE_RUN_STATUSES:
        caveats.append(
            f"The scan ended with status '{status}' rather than completing, so coverage "
            "reflects only the work finished before it stopped."
        )
    unfinished = [agent for agent in agents if agent["status"] in _INCOMPLETE_AGENT_STATUSES]
    if unfinished:
        names = ", ".join(sorted(str(agent["agent_name"]) for agent in unfinished))
        caveats.append(
            f"{len(unfinished)} agent(s) did not finish cleanly ({names}); any surface they "
            "held is under-covered."
        )
    if exit_reason and exit_reason not in {"finished_by_tool", "completed"}:
        caveats.append(
            f"The run terminated via '{exit_reason}' rather than the root agent finishing, "
            "so remaining scope was not reached."
        )

    return {
        "complete": not caveats,
        "scan_status": status,
        "exit_reason": exit_reason,
        "caveats": caveats,
    }


def _outcome_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        outcome = str(entry.get("outcome", ""))
        counts[outcome] = counts.get(outcome, 0) + 1
    return {label: counts[label] for label in OUTCOME_LABELS if label in counts}


def build_coverage_document(
    *,
    run_record: dict[str, Any],
    entries: list[dict[str, Any]],
    agent_graph: dict[str, Any],
    vulnerability_reports: list[dict[str, Any]],
    exit_reason: str | None = None,
) -> dict[str, Any]:
    """Assemble the ``coverage.json`` document."""
    agents = agents_from_graph(agent_graph)
    skills_exercised = sorted(
        {_skill_leaf(skill) for agent in agents for skill in agent["skills"] if skill}
    )

    ledger = [
        {
            "surface": entry.get("surface", ""),
            "risk_area": entry.get("risk_area", ""),
            "outcome": entry.get("outcome", ""),
            "outcome_label": OUTCOME_LABELS.get(str(entry.get("outcome", "")), ""),
            "evidence": entry.get("evidence", ""),
            "recorded_by": entry.get("agent_name", ""),
            "recorded_at": entry.get("created_at", ""),
            "updated_at": entry.get("updated_at", ""),
            "previous_outcomes": [
                str(previous.get("outcome", ""))
                for previous in entry.get("history", [])
                if isinstance(previous, dict)
            ],
            "source": "agent_reported",
        }
        for entry in entries
    ]

    gaps = [
        *_unresolved_gaps(entries),
        *skill_coverage_gaps(entries, agents),
        *_silent_agent_gaps(entries, agents),
    ]

    return {
        "schema_version": COVERAGE_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "run_id": run_record.get("run_id"),
        "run_name": run_record.get("run_name"),
        "scope": {
            "targets": run_record.get("targets_info") or [],
            "scan_mode": run_record.get("scan_mode"),
            "scope_mode": run_record.get("scope_mode"),
            "diff_scope": run_record.get("diff_scope"),
            "instruction": run_record.get("instruction") or "",
        },
        "summary": {
            "surfaces_reviewed": len(ledger),
            "outcomes": _outcome_counts(entries),
            "findings_filed": len(vulnerability_reports),
            "gaps": len(gaps),
        },
        "machine_observed": {
            "agents": agents,
            "skills_exercised": skills_exercised,
            "findings_filed": len(vulnerability_reports),
            "source": "runtime",
        },
        "completeness": _completeness(run_record, agents, exit_reason),
        "entries": ledger,
        "gaps": gaps,
    }


def write_coverage(run_dir: Path, document: dict[str, Any]) -> Path:
    """Write ``coverage.json`` into the run directory and return its path."""
    path = run_dir / COVERAGE_FILENAME
    atomic_write_text(path, json.dumps(document, ensure_ascii=False, indent=2, default=str))
    logger.info(
        "Saved coverage record to: %s (%d surface(s), %d gap(s))",
        path,
        len(document.get("entries", [])),
        len(document.get("gaps", [])),
    )
    return path
