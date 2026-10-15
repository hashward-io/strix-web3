"""Local-only telemetry facade.

The self-hosted Web3 audit engine collects no usage telemetry. This package
retains the historical import surface — ``report_error``, ``set_scan_phase``,
and the ``posthog``/``scarf`` names — so existing call sites keep working, but
every function is a no-op. Nothing is sent anywhere.
"""

from . import posthog, scarf
from ._common import set_scan_phase


def report_error(error_type: str, exc: BaseException | None = None) -> None:
    """Record a failure category locally. No data leaves the sandbox."""
    posthog.error(error_type, exc)
    scarf.error(error_type, exc)


__all__ = [
    "posthog",
    "report_error",
    "scarf",
    "set_scan_phase",
]
