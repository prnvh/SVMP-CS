"""Unit tests for high-level intent routing."""

from __future__ import annotations

import pytest

from svmp_core.core import IntentType, infer_intent
from svmp_core.exceptions import RoutingError


def test_infer_intent_marks_informational_questions() -> None:
    """FAQ-style questions should take the informational branch."""

    assert infer_intent("What is your return policy?") == IntentType.INFORMATIONAL


def test_infer_intent_marks_transactional_requests() -> None:
    """Action-oriented requests should take the transactional branch."""

    assert infer_intent("Please cancel my order") == IntentType.TRANSACTIONAL


def test_infer_intent_handles_punctuation_in_transactional_requests() -> None:
    """Punctuation should not hide obvious transactional keywords."""

    assert infer_intent("Refund!") == IntentType.TRANSACTIONAL


def test_infer_intent_treats_questions_about_actions_as_informational() -> None:
    """Question-style asks about an action should stay on the informational branch."""

    assert infer_intent("How do I cancel my order?") == IntentType.INFORMATIONAL


def test_infer_intent_uses_safe_escalate_fallback() -> None:
    """Ambiguous input should not be force-classified aggressively."""

    assert infer_intent("hello") == IntentType.ESCALATE


def test_infer_intent_rejects_blank_query() -> None:
    """Blank input should fail fast."""

    with pytest.raises(RoutingError, match="query must not be blank"):
        infer_intent("   ")
