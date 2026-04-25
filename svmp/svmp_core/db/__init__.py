"""Database contracts and adapters for the SVMP core."""

from __future__ import annotations

from svmp_core.db.base import (
    AuditLogRepository,
    BillingSubscriptionRepository,
    Database,
    GovernanceLogRepository,
    KnowledgeBaseRepository,
    ProviderEventRepository,
    SessionStateRepository,
    TenantRepository,
)

__all__ = [
    "AuditLogRepository",
    "BillingSubscriptionRepository",
    "Database",
    "GovernanceLogRepository",
    "KnowledgeBaseRepository",
    "ProviderEventRepository",
    "SessionStateRepository",
    "SupabaseDatabase",
    "TenantRepository",
]


def __getattr__(name: str):
    """Load concrete adapters lazily so contract imports stay lightweight."""

    if name == "SupabaseDatabase":
        from svmp_core.db.supabase import SupabaseDatabase

        return SupabaseDatabase
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
