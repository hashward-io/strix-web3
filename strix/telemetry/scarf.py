"""No-op telemetry stub.

The self-hosted Web3 audit engine sends no usage telemetry. This module keeps
the historical ``scarf`` call sites working by accepting the same arguments and
doing nothing — no network, no data leaves the sandbox.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from strix.report.state import ReportState


def start(*args: Any, **kwargs: Any) -> None:
    """Previously initialized the Scarf client. Now a no-op."""


def finding(severity: str, cwe: str | None = None, is_cve: bool = False) -> None:
    """Previously reported a finding. Now a no-op."""


def end(report_state: ReportState, exit_reason: str = "completed") -> None:
    """Previously reported scan end. Now a no-op."""


def error(error_type: str, exc: BaseException | None = None) -> None:
    """Previously reported a failure category. Now a no-op."""
