"""Run-scoped invariant catalog — mirrored to ``{state_dir}/invariants.json``.

An invariant is a property of the protocol that must hold across any sequence of
calls: a conservation law (``total == Σ balances``), a bound (``withdrawable <=
deposited``), a ratio, a state-machine latch, a temporal constraint, or a
cross-contract / economic assumption. The invariant catalog is the spine of a
smart-contract audit: recon derives it, the lens passes test it, and the report
states what held and what did not.

One agent records an invariant and every other agent on the same run reads it
back instead of re-deriving it. The store does not outlive the scan; the mirror
under the run's state directory exists only so a resumed scan keeps the catalog
its earlier agents agreed on, and the client-facing artifact is written with the
report. Entries are agent-reported self-reports, paired with machine-observed
facts at report time.
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents import RunContextWrapper, function_tool


logger = logging.getLogger(__name__)


_invariants_storage: dict[str, dict[str, Any]] = {}
_invariants_lock = threading.RLock()
_invariants_path: Path | None = None
_ENTRY_ID_GENERATION_ATTEMPTS = 1024

VALID_KINDS: tuple[str, ...] = (
    "conservation",
    "bound",
    "ratio",
    "state_machine",
    "temporal",
    "cross_contract",
    "economic",
)

VALID_STATUSES: tuple[str, ...] = (
    "unproven",
    "holding",
    "broken",
    "not_applicable",
)

_STATUSES_REQUIRING_EVIDENCE = frozenset({"holding", "broken", "not_applicable"})


def _caller_identity(ctx: RunContextWrapper) -> tuple[str | None, str | None]:
    """Return the (agent_id, agent_name) of the agent invoking this tool."""
    inner = ctx.context if isinstance(ctx.context, dict) else {}
    raw_agent_id = inner.get("agent_id")
    agent_id = raw_agent_id if isinstance(raw_agent_id, str) else None
    agent_name: str | None = None
    coordinator = inner.get("coordinator")
    if agent_id is not None and coordinator is not None:
        names = getattr(coordinator, "names", {})
        if isinstance(names, dict):
            raw_agent_name = names.get(agent_id)
            agent_name = raw_agent_name if isinstance(raw_agent_name, str) else None
    return agent_id, agent_name


def _generate_entry_id() -> str | None:
    """Allocate an unused entry id. Callers must already hold ``_invariants_lock``."""
    for _ in range(_ENTRY_ID_GENERATION_ATTEMPTS):
        entry_id = uuid.uuid4().hex[:6]
        if entry_id not in _invariants_storage:
            return entry_id
    return None


def hydrate_invariants_from_disk(state_dir: Path) -> None:
    global _invariants_path  # noqa: PLW0603
    _invariants_path = state_dir / "invariants.json"
    with _invariants_lock:
        _invariants_storage.clear()
        if not _invariants_path.exists():
            return
        try:
            data = json.loads(_invariants_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.exception(
                "invariants.json at %s is unreadable; starting with empty catalog",
                _invariants_path,
            )
            return
        if not isinstance(data, dict):
            return
        _invariants_storage.update(
            {
                eid: entry
                for eid, entry in data.items()
                if isinstance(eid, str) and isinstance(entry, dict)
            }
        )
        logger.info(
            "invariants hydrated from %s (%d entr(ies))",
            _invariants_path,
            len(_invariants_storage),
        )


def _persist_locked() -> None:
    """Mirror the catalog to disk. Callers must already hold ``_invariants_lock``."""
    path = _invariants_path
    if path is None:
        return
    try:
        payload = json.dumps(_invariants_storage, ensure_ascii=False, default=str)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(payload)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
    except Exception:
        logger.exception("invariant catalog persist to %s failed", path)


def get_invariant_entries() -> list[dict[str, Any]]:
    """Return every invariant entry, newest last. Used by ``finish_scan``."""
    with _invariants_lock:
        entries = [{**entry, "entry_id": eid} for eid, entry in _invariants_storage.items()]
    entries.sort(key=lambda e: str(e.get("created_at", "")))
    return entries


def status_counts() -> dict[str, int]:
    """Count invariants per status, in the canonical status order."""
    counts: dict[str, int] = {}
    for entry in get_invariant_entries():
        status = str(entry.get("status", "")).lower()
        counts[status] = counts.get(status, 0) + 1
    return {s: counts[s] for s in VALID_STATUSES if s in counts}


def _validate(
    *, kind: str, statement: str, locations: str, status: str, evidence: str
) -> tuple[str, str, list[str]]:
    errors: list[str] = []
    normalized_kind = kind.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized_kind not in VALID_KINDS:
        errors.append(f"Invalid kind: {kind!r}. Must be one of: {list(VALID_KINDS)}")
    if not statement.strip():
        errors.append("statement cannot be empty - state the property in one sentence")
    normalized_status = status.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized_status not in VALID_STATUSES:
        errors.append(f"Invalid status: {status!r}. Must be one of: {list(VALID_STATUSES)}")
    elif normalized_status in _STATUSES_REQUIRING_EVIDENCE and not evidence.strip():
        errors.append(
            f"evidence is required for status '{normalized_status}' - say what proves it "
            "holds, what breaks it, or why it does not apply"
        )
    if normalized_status == "broken" and not locations.strip():
        errors.append(
            "locations is required for a broken invariant - name the Contract.function "
            "site whose write does not enforce it"
        )
    return normalized_kind, normalized_status, errors


def _duplicate_of_locked(kind: str, statement: str) -> tuple[str, dict[str, Any]] | None:
    """Find an existing catalog row for the same statement (case-insensitive).

    Callers must already hold ``_invariants_lock``. The uniqueness check and the
    insertion that depends on it have to be one critical section.
    """
    key = (kind.strip().lower(), statement.strip().lower())
    for entry_id, entry in _invariants_storage.items():
        existing = (
            str(entry.get("kind", "")).strip().lower(),
            str(entry.get("statement", "")).strip().lower(),
        )
        if existing == key:
            return entry_id, dict(entry)
    return None


def _record_impl(
    *,
    kind: str,
    statement: str,
    locations: str,
    status: str,
    evidence: str,
    agent_id: str | None,
    agent_name: str | None,
) -> dict[str, Any]:
    normalized_kind, normalized_status, errors = _validate(
        kind=kind,
        statement=statement,
        locations=locations,
        status=status,
        evidence=evidence,
    )
    if errors:
        return {"success": False, "error": "Validation failed", "errors": errors}

    entry: dict[str, Any] = {
        "kind": normalized_kind,
        "statement": statement.strip(),
        "status": normalized_status,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    if locations.strip():
        entry["locations"] = locations.strip()
    if evidence.strip():
        entry["evidence"] = evidence.strip()
    if agent_id:
        entry["agent_id"] = agent_id
    if agent_name:
        entry["agent_name"] = agent_name

    with _invariants_lock:
        duplicate = _duplicate_of_locked(normalized_kind, statement)
        if duplicate is not None:
            existing_id, existing = duplicate
            return {
                "success": False,
                "error": (
                    f"Invariant already recorded as {existing_id} "
                    f"({existing.get('kind', '')}, currently '{existing.get('status', '')}'). "
                    "If your testing changes the verdict, move that entry with "
                    f"update_invariant(entry_id='{existing_id}', ...) instead of "
                    "recording a second row for the same property."
                ),
                "existing_entry_id": existing_id,
                "existing_status": existing.get("status", ""),
            }

        entry_id = _generate_entry_id()
        if entry_id is None:
            return {"success": False, "error": "Could not allocate an invariant entry id"}
        _invariants_storage[entry_id] = entry
        _persist_locked()
    logger.info(
        "Invariant recorded: id=%s kind=%s status=%s",
        entry_id,
        normalized_kind,
        normalized_status,
    )
    return {
        "success": True,
        "entry_id": entry_id,
        "kind": normalized_kind,
        "status": normalized_status,
        "message": f"Invariant recorded ({normalized_kind}, {normalized_status})",
    }


def _update_impl(
    *,
    entry_id: str,
    status: str,
    evidence: str,
    locations: str,
    agent_id: str | None,
    agent_name: str | None,
) -> dict[str, Any]:
    key = (entry_id or "").strip()
    with _invariants_lock:
        existing = _invariants_storage.get(key)
        if existing is None:
            return {
                "success": False,
                "error": (
                    f"No invariant entry {entry_id!r}. Call list_invariants to find the "
                    "entry you mean."
                ),
            }
        kind = str(existing.get("kind", ""))
        statement = str(existing.get("statement", ""))
        merged_locations = locations.strip() or str(existing.get("locations", ""))
        _normalized_kind, normalized_status, errors = _validate(
            kind=kind,
            statement=statement,
            locations=merged_locations,
            status=status,
            evidence=evidence,
        )
        if errors:
            return {"success": False, "error": "Validation failed", "errors": errors}

        previous_status = str(existing.get("status", ""))
        superseded: dict[str, Any] = {
            "status": previous_status,
            "recorded_at": existing.get("created_at", ""),
        }
        if existing.get("evidence"):
            superseded["evidence"] = existing["evidence"]
        if existing.get("agent_name"):
            superseded["agent_name"] = existing["agent_name"]
        history = existing.get("history")
        existing["history"] = [*history, superseded] if isinstance(history, list) else [superseded]

        existing["status"] = normalized_status
        existing["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        if locations.strip():
            existing["locations"] = locations.strip()
        if evidence.strip():
            existing["evidence"] = evidence.strip()
        if agent_id:
            existing["agent_id"] = agent_id
        if agent_name:
            existing["agent_name"] = agent_name
        _persist_locked()
    logger.info(
        "Invariant updated: id=%s %s -> %s",
        key,
        previous_status,
        normalized_status,
    )
    return {
        "success": True,
        "entry_id": key,
        "previous_status": previous_status,
        "status": normalized_status,
        "message": (
            f"Invariant moved from {previous_status} to {normalized_status}. "
            "The previous state is kept as history."
        ),
    }


def _list_impl(
    *, kind: str | None, status: str | None, caller_agent_id: str | None
) -> dict[str, Any]:
    normalized_kind: str | None = None
    if kind and kind.strip():
        normalized_kind = kind.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized_kind not in VALID_KINDS:
            return {
                "success": False,
                "error": f"Invalid kind: {kind!r}. Must be one of: {list(VALID_KINDS)}",
            }
    normalized_status: str | None = None
    if status and status.strip():
        normalized_status = status.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized_status not in VALID_STATUSES:
            return {
                "success": False,
                "error": f"Invalid status: {status!r}. Must be one of: {list(VALID_STATUSES)}",
            }

    entries: list[dict[str, Any]] = []
    for entry in get_invariant_entries():
        if normalized_kind and entry.get("kind") != normalized_kind:
            continue
        if normalized_status and entry.get("status") != normalized_status:
            continue
        listing = {
            "entry_id": entry.get("entry_id"),
            "kind": entry.get("kind", ""),
            "statement": entry.get("statement", ""),
            "status": entry.get("status", ""),
            "locations": entry.get("locations", ""),
            "created_at": entry.get("created_at", ""),
        }
        evidence = str(entry.get("evidence", ""))
        if evidence:
            listing["evidence"] = evidence
        agent_name = entry.get("agent_name")
        if agent_name:
            listing["agent_name"] = agent_name
        history = entry.get("history")
        if isinstance(history, list) and history:
            listing["previous_statuses"] = [str(h.get("status", "")) for h in history]
        if caller_agent_id is not None and entry.get("agent_id") == caller_agent_id:
            listing["by_you"] = True
        entries.append(listing)

    return {
        "success": True,
        "entries": entries,
        "filtered_count": len(entries),
        "total_count": len(_invariants_storage),
        "status_counts": status_counts(),
    }


@function_tool(timeout=30)
async def record_invariant(
    ctx: RunContextWrapper,
    kind: str,
    statement: str,
    locations: str = "",
    status: str = "unproven",
    evidence: str = "",
) -> str:
    """Record a protocol invariant in the scan's shared catalog.

    The invariant catalog is the spine of a smart-contract audit. Before
    hunting bugs, enumerate the properties the protocol must always
    hold, and record each one here with the sites that write the
    constrained state. The lens passes then read the catalog and try to
    break it; the root agent reconciles it before finishing.

    Record invariants as you derive them, not in a batch at the end.
    Entries are shared across every agent in the scan.

    If this property already has a row, this call is rejected and returns
    that row's id — move it with ``update_invariant`` instead, so the
    catalog does not show a stale verdict beside its replacement.

    **Kinds** (pick exactly one):

    - ``conservation`` — a value is conserved (``total == Σ balances``,
      ``ΔA == -ΔB``).
    - ``bound`` — an inequality holds (``withdrawable <= deposited``).
    - ``ratio`` — a derived ratio is correct and uses the right snapshot.
    - ``state_machine`` — a one-shot latch or legal state transition.
    - ``temporal`` — a time/epoch constraint (deadlines, lockups).
    - ``cross_contract`` — an assumption one contract makes about another.
    - ``economic`` — a higher-order property built on the others.

    **Status** (pick exactly one):

    - ``unproven`` — derived but not yet tested (the default).
    - ``holding`` — testing found no counterexample. Name the test and
      its bounds in ``evidence`` (a fuzz run is evidence, not proof).
    - ``broken`` — you found a counterexample. Name the violating
      ``Contract.function`` in ``locations`` and file the finding.
    - ``not_applicable`` — the property cannot apply here; say why.

    Args:
        kind: One of ``conservation`` / ``bound`` / ``ratio`` /
            ``state_machine`` / ``temporal`` / ``cross_contract`` /
            ``economic``.
        statement: The property in one sentence, e.g. ``totalAssets()
            >= totalDeposits()`` or ``sum(userShares) == totalSupply``.
        locations: The ``Contract.function`` sites that write the
            constrained state. Required for a ``broken`` invariant.
        status: One of ``unproven`` / ``holding`` / ``broken`` /
            ``not_applicable``. Defaults to ``unproven``.
        evidence: How you know. Required for ``holding`` / ``broken`` /
            ``not_applicable`` — name the test and its bounds, the
            counterexample, or the reason it does not apply.
    """
    agent_id, agent_name = _caller_identity(ctx)
    result = await asyncio.to_thread(
        _record_impl,
        kind=kind,
        statement=statement,
        locations=locations,
        status=status,
        evidence=evidence,
        agent_id=agent_id,
        agent_name=agent_name,
    )
    return json.dumps(result, ensure_ascii=False, default=str)


@function_tool(timeout=30)
async def update_invariant(
    ctx: RunContextWrapper,
    entry_id: str,
    status: str,
    evidence: str = "",
    locations: str = "",
) -> str:
    """Change the verdict on an already-recorded invariant.

    The catalog is shared across the whole agent tree, and an
    invariant's status is not final when first written. Use this
    whenever later work changes the answer:

    - You tested an ``unproven`` invariant and it held (or broke).
    - You picked up someone else's invariant and found the write site
      that does not enforce it.
    - You disproved a ``holding`` row — testing was incomplete, or the
      property only holds under an assumption that fails.

    Find the id with ``list_invariants``, then update it. Do not record
    a fresh row for the same property; that leaves a stale entry beside
    its own replacement.

    The previous status, evidence, and author are kept as history.

    Args:
        entry_id: The id of the entry to update, from ``list_invariants``.
        status: The new status — ``unproven`` / ``holding`` / ``broken``
            / ``not_applicable``.
        evidence: How you know, now. Required for ``holding`` /
            ``broken`` / ``not_applicable``. Say what changed.
        locations: Optionally refine the write sites. Required to mark a
            row ``broken`` when the existing row had none.
    """
    agent_id, agent_name = _caller_identity(ctx)
    result = await asyncio.to_thread(
        _update_impl,
        entry_id=entry_id,
        status=status,
        evidence=evidence,
        locations=locations,
        agent_id=agent_id,
        agent_name=agent_name,
    )
    return json.dumps(result, ensure_ascii=False, default=str)


@function_tool(timeout=30)
async def list_invariants(
    ctx: RunContextWrapper,
    kind: str | None = None,
    status: str | None = None,
) -> str:
    """List invariants recorded in this scan's catalog.

    **For the orchestrator / root agent**, and for any agent deciding
    what to test next. Use it to see which properties have been derived,
    which are still ``unproven``, and which have been broken. Before
    finishing, every ``unproven`` invariant is either a lead worth a
    follow-up agent or a row testing has refuted.

    Returns each entry with its ``kind``, ``statement``, ``status``,
    ``locations``, evidence, and the agent that recorded it, plus
    ``status_counts`` across the whole catalog.

    Args:
        kind: Optional filter — one of ``conservation`` / ``bound`` /
            ``ratio`` / ``state_machine`` / ``temporal`` /
            ``cross_contract`` / ``economic``.
        status: Optional filter — one of ``unproven`` / ``holding`` /
            ``broken`` / ``not_applicable``. Filter on ``unproven``
            before finishing to see what is still open.
    """
    caller_agent_id, _ = _caller_identity(ctx)
    result = await asyncio.to_thread(
        _list_impl, kind=kind, status=status, caller_agent_id=caller_agent_id
    )
    return json.dumps(result, ensure_ascii=False, default=str)
