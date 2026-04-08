"""Deterministic red-flag escalation signals for inbound support traffic."""

from __future__ import annotations

from dataclasses import dataclass

from svmp_core.models.session import MessageItem

_WRONG_ANSWER_PHRASES = (
    "wrong answer",
    "that is wrong",
    "this is wrong",
    "incorrect answer",
    "not the right answer",
    "you got it wrong",
)

_HUMAN_HANDOFF_PHRASES = (
    "connect me to support"
)

_PROFANITY_TERMS = (
    "fuck",
    "fucking",
    "shit",
    "bitch",
    "asshole",
    "motherfucker",
    "mc",
    "bc",
)


@dataclass(frozen=True)
class RedFlagDecision:
    """Normalized outcome from deterministic red-flag detection."""

    should_escalate: bool
    reason: str | None
    matched_signals: list[str]
    bypass_faq: bool


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> list[str]:
    """Return all phrases found in the normalized text."""

    return [phrase for phrase in phrases if phrase in text]


def evaluate_red_flags(messages: list[MessageItem], active_question: str) -> RedFlagDecision:
    """Detect deterministic red flags before FAQ matching."""

    normalized_question = active_question.strip().lower()

    media_messages = [
        message
        for message in messages
        if (message.message_type or "text").strip().lower() != "text"
    ]
    if media_messages:
        first_media = media_messages[0]
        message_type = (first_media.message_type or "media").strip().lower()
        return RedFlagDecision(
            should_escalate=True,
            reason=f"{message_type}_received",
            matched_signals=[f"message_type:{message_type}"],
            bypass_faq=True,
        )

    if normalized_question:
        wrong_answer_matches = _contains_phrase(normalized_question, _WRONG_ANSWER_PHRASES)
        if wrong_answer_matches:
            return RedFlagDecision(
                should_escalate=True,
                reason="wrong_answer_reported",
                matched_signals=[f"phrase:{match}" for match in wrong_answer_matches],
                bypass_faq=True,
            )

        handoff_matches = _contains_phrase(normalized_question, _HUMAN_HANDOFF_PHRASES)
        if handoff_matches:
            return RedFlagDecision(
                should_escalate=True,
                reason="human_handoff_requested",
                matched_signals=[f"phrase:{match}" for match in handoff_matches],
                bypass_faq=True,
            )

        profanity_matches = _contains_phrase(normalized_question, _PROFANITY_TERMS)
        if profanity_matches:
            return RedFlagDecision(
                should_escalate=True,
                reason="profanity_detected",
                matched_signals=[f"term:{match}" for match in profanity_matches],
                bypass_faq=True,
            )

    return RedFlagDecision(
        should_escalate=False,
        reason=None,
        matched_signals=[],
        bypass_faq=False,
    )
