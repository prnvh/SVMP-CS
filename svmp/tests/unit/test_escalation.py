"""Unit tests for the escalation stub."""

from __future__ import annotations

import pytest

from svmp_core.core import EscalationTarget, IdentityFrame, request_escalation
from svmp_core.exceptions import EscalationError


def _identity() -> IdentityFrame:
    """Build a canonical identity frame for escalation tests."""

    return IdentityFrame(
        tenant_id="Niyomilan",
        client_id="whatsapp",
        user_id="9845891194",
    )


def test_request_escalation_returns_predictable_stub_result() -> None:
    """The stub should normalize input and return a human-review result."""

    result = request_escalation(
        _identity(),
        " I need a refund ",
        reason=" low_confidence ",
        metadata={"score": 0.41},
    )

    assert result.escalated is True
    assert result.target == EscalationTarget.HUMAN_REVIEW
    assert result.reason == "low_confidence"
    assert result.ticket_reference is None
    assert result.metadata == {"score": 0.41}


def test_request_escalation_rejects_blank_combined_text() -> None:
    """Blank combined text should fail fast."""

    with pytest.raises(EscalationError, match="combined_text must not be blank"):
        request_escalation(
            _identity(),
            "   ",
            reason="low_confidence",
        )


def test_request_escalation_rejects_blank_reason() -> None:
    """Blank reasons should fail fast."""

    with pytest.raises(EscalationError, match="reason must not be blank"):
        request_escalation(
            _identity(),
            "I need a refund",
            reason="   ",
        )
