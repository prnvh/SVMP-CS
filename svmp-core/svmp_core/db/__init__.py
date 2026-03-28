"""Database contracts for the SVMP core."""

from svmp_core.db.base import (
    Database,
    GovernanceLogRepository,
    KnowledgeBaseRepository,
    SessionStateRepository,
    TenantRepository,
)

__all__ = [
    "Database",
    "GovernanceLogRepository",
    "KnowledgeBaseRepository",
    "SessionStateRepository",
    "TenantRepository",
]
