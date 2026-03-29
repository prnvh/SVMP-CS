"""Helpers for building governance log records consistently."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from svmp_core.core.identity_frame import IdentityFrame
from svmp_core.models.governance import GovernanceDecision, GovernanceLog


def build_governance_log(
    identity: IdentityFrame,
    decision: GovernanceDecision,
    combined_text: str,
    *,
    similarity_score: float | None = None,
    answer_supplied: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> GovernanceLog:
    """Build a normalized governance log from a validated identity frame."""

    normalized_text = combined_text.strip()
    if not normalized_text:
        raise ValueError("combined_text must not be blank")

    return GovernanceLog(
        tenant_id=identity.tenant_id,
        client_id=identity.client_id,
        user_id=identity.user_id,
        decision=decision,
        similarity_score=similarity_score,
        combined_text=normalized_text,
        answer_supplied=answer_supplied,
        metadata=deepcopy(dict(metadata or {})),
        timestamp=timestamp or datetime.now(timezone.utc),
    )


def build_answered_log(
    identity: IdentityFrame,
    combined_text: str,
    *,
    similarity_score: float,
    answer_supplied: str,
    metadata: Mapping[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> GovernanceLog:
    """Build a governance log for a successful automated answer."""

    return build_governance_log(
        identity,
        GovernanceDecision.ANSWERED,
        combined_text,
        similarity_score=similarity_score,
        answer_supplied=answer_supplied,
        metadata=metadata,
        timestamp=timestamp,
    )


def build_escalated_log(
    identity: IdentityFrame,
    combined_text: str,
    *,
    similarity_score: float | None = None,
    metadata: Mapping[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> GovernanceLog:
    """Build a governance log for an escalation outcome."""

    return build_governance_log(
        identity,
        GovernanceDecision.ESCALATED,
        combined_text,
        similarity_score=similarity_score,
        metadata=metadata,
        timestamp=timestamp,
    )


def build_closed_log(
    identity: IdentityFrame,
    combined_text: str,
    *,
    metadata: Mapping[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> GovernanceLog:
    """Build a governance log for session closure."""

    return build_governance_log(
        identity,
        GovernanceDecision.CLOSED,
        combined_text,
        metadata=metadata,
        timestamp=timestamp,
    )
