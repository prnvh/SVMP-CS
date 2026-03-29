"""Stub escalation helpers for workflow fallback handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from svmp_core.core.identity_frame import IdentityFrame
from svmp_core.exceptions import EscalationError


class EscalationTarget(StrEnum):
    """Supported fallback targets for early escalation handling."""

    HUMAN_REVIEW = "human_review"


@dataclass(frozen=True)
class EscalationRequest:
    """Normalized escalation request built from workflow context."""

    identity: IdentityFrame
    combined_text: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EscalationResult:
    """Predictable result returned by the escalation stub."""

    escalated: bool
    target: EscalationTarget
    reason: str
    ticket_reference: str | None
    metadata: dict[str, Any] = field(default_factory=dict)


def request_escalation(
    identity: IdentityFrame,
    combined_text: str,
    *,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> EscalationResult:
    """Validate and normalize a request for human escalation."""

    normalized_text = combined_text.strip()
    normalized_reason = reason.strip()

    if not normalized_text:
        raise EscalationError("combined_text must not be blank")
    if not normalized_reason:
        raise EscalationError("reason must not be blank")

    request = EscalationRequest(
        identity=identity,
        combined_text=normalized_text,
        reason=normalized_reason,
        metadata=dict(metadata or {}),
    )

    return EscalationResult(
        escalated=True,
        target=EscalationTarget.HUMAN_REVIEW,
        reason=request.reason,
        ticket_reference=None,
        metadata=request.metadata,
    )
