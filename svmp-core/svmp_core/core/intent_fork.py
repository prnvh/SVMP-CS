"""Intent routing helpers for deciding answer-vs-action behavior."""

from __future__ import annotations

import re
from enum import StrEnum

from svmp_core.exceptions import RoutingError


class IntentType(StrEnum):
    """Supported high-level intent branches for Workflow B."""

    INFORMATIONAL = "informational"
    TRANSACTIONAL = "transactional"
    ESCALATE = "escalate"


_TRANSACTIONAL_KEYWORDS = {
    "cancel",
    "change",
    "exchange",
    "refund",
    "replace",
    "reschedule",
    "return",
    "track",
    "update",
}

_INFORMATIONAL_KEYWORDS = {
    "about",
    "can",
    "contact",
    "does",
    "do",
    "hours",
    "how",
    "is",
    "policy",
    "price",
    "pricing",
    "ship",
    "shipping",
    "what",
    "when",
    "where",
}

_QUESTION_CUES = {"can", "do", "does", "how", "is", "what", "when", "where", "why"}
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(value: str) -> set[str]:
    """Split text into lowercase word tokens without punctuation noise."""

    return set(_TOKEN_PATTERN.findall(value.lower()))


def infer_intent(query: str) -> IntentType:
    """Classify a query into a safe high-level intent branch."""

    normalized = query.strip().lower()
    if not normalized:
        raise RoutingError("query must not be blank")

    tokens = _tokenize(normalized)
    transactional_score = len(tokens & _TRANSACTIONAL_KEYWORDS)
    informational_score = len(tokens & _INFORMATIONAL_KEYWORDS)
    is_question_style = normalized.endswith("?") or bool(tokens & _QUESTION_CUES)

    if transactional_score == 0 and informational_score == 0:
        return IntentType.ESCALATE

    if transactional_score > informational_score:
        return IntentType.TRANSACTIONAL

    if informational_score > transactional_score:
        return IntentType.INFORMATIONAL

    if is_question_style:
        return IntentType.INFORMATIONAL

    return IntentType.ESCALATE
