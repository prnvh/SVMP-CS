"""Core domain helpers for the SVMP runtime."""

from svmp_core.core.governance import (
    build_answered_log,
    build_closed_log,
    build_escalated_log,
    build_governance_log,
)
from svmp_core.core.identity_frame import IdentityFrame
from svmp_core.core.similarity_gate import SimilarityDecision, SimilarityOutcome, evaluate_similarity

__all__ = [
    "IdentityFrame",
    "SimilarityDecision",
    "SimilarityOutcome",
    "build_answered_log",
    "build_closed_log",
    "build_escalated_log",
    "build_governance_log",
    "evaluate_similarity",
]
