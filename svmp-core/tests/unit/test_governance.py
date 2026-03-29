"""Unit tests for governance log helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from svmp_core.core import (
    IdentityFrame,
    build_answered_log,
    build_closed_log,
    build_escalated_log,
    build_governance_log,
)
from svmp_core.models import GovernanceDecision


def _identity() -> IdentityFrame:
    """Build a canonical identity frame for tests."""

    return IdentityFrame(
        tenant_id="Niyomilan",
        client_id="whatsapp",
        user_id="9845891194",
    )


def test_build_governance_log_uses_identity_frame_fields() -> None:
    """The base helper should map identity values into the governance log."""

    timestamp = datetime(2026, 3, 30, tzinfo=timezone.utc)

    log = build_governance_log(
        _identity(),
        GovernanceDecision.ESCALATED,
        "Need human help",
        similarity_score=0.42,
        metadata={"route": "ops"},
        timestamp=timestamp,
    )

    assert log.tenant_id == "Niyomilan"
    assert log.client_id == "whatsapp"
    assert log.user_id == "9845891194"
    assert log.decision == GovernanceDecision.ESCALATED
    assert log.similarity_score == 0.42
    assert log.metadata == {"route": "ops"}
    assert log.timestamp == timestamp


def test_build_answered_log_sets_answer_specific_fields() -> None:
    """Answered logs should carry score and supplied answer."""

    log = build_answered_log(
        _identity(),
        "what do you do",
        similarity_score=0.91,
        answer_supplied="We help customers.",
    )

    assert log.decision == GovernanceDecision.ANSWERED
    assert log.similarity_score == 0.91
    assert log.answer_supplied == "We help customers."


def test_build_escalated_log_leaves_answer_empty() -> None:
    """Escalated logs should not require an answer payload."""

    log = build_escalated_log(
        _identity(),
        "I need a refund",
        similarity_score=0.32,
    )

    assert log.decision == GovernanceDecision.ESCALATED
    assert log.answer_supplied is None


def test_build_closed_log_sets_closed_decision() -> None:
    """Closed logs should mark the closure outcome cleanly."""

    log = build_closed_log(
        _identity(),
        "stale session closed",
        metadata={"retentionHours": 24},
    )

    assert log.decision == GovernanceDecision.CLOSED
    assert log.similarity_score is None
    assert log.metadata == {"retentionHours": 24}


def test_build_governance_log_rejects_blank_combined_text() -> None:
    """Blank combined text should fail fast."""

    with pytest.raises(ValueError, match="combined_text must not be blank"):
        build_governance_log(
            _identity(),
            GovernanceDecision.ANSWERED,
            "   ",
        )
