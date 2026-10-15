"""No-op telemetry stub.

The self-hosted Web3 audit engine sends no usage telemetry. This module keeps
the historical ``posthog`` call sites working by accepting the same arguments
and doing nothing — no network, no data leaves the sandbox.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from strix.report.state import ReportState


def start(*args: Any, **kwargs: Any) -> None:
    """Previously initialized the PostHog client. Now a no-op."""


def finding(severity: str, cwe: str | None = None, is_cve: bool = False) -> None:
    """Previously reported a finding. Now a no-op."""


def end(report_state: ReportState, exit_reason: str = "completed") -> None:
    """Previously reported scan end. Now a no-op."""


def viewer_opened(source: str, live: bool) -> None:
    """Previously reported the viewer opening. Now a no-op."""


def viewer_cta_clicked(cta: str, surface: str | None = None) -> None:
    """Previously reported a viewer CTA click. Now a no-op."""


def viewer_email_event(step: str, purpose: str | None = None) -> None:
    """Previously reported a viewer email event. Now a no-op."""


def viewer_feedback_submitted() -> None:
    """Previously reported viewer feedback. Now a no-op."""


def viewer_agent_steered() -> None:
    """Previously reported agent steering from the viewer. Now a no-op."""


def error(error_type: str, exc: BaseException | None = None) -> None:
    """Previously reported a failure category. Now a no-op."""
