"""Dashboard API routes for the SVMP customer portal."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import APIRouter, Depends

from svmp_core.auth import (
    ACTIVE_SUBSCRIPTION_STATUSES,
    PortalRole,
    TenantContext,
    require_tenant_context,
)


def _allowed_actions(context: TenantContext) -> list[str]:
    """Return user-facing action ids permitted for the current context."""

    if context.subscription_status not in ACTIVE_SUBSCRIPTION_STATUSES:
        return [
            "billing.read",
            "billing.checkout",
            "billing.portal",
        ]

    actions_by_role: dict[PortalRole, Iterable[str]] = {
        PortalRole.OWNER: [
            "billing.manage",
            "team.manage",
            "integrations.manage",
            "knowledge_base.manage",
            "brand_voice.manage",
            "settings.manage",
            "sessions.read",
            "metrics.read",
            "governance.read",
        ],
        PortalRole.ADMIN: [
            "integrations.manage",
            "knowledge_base.manage",
            "brand_voice.manage",
            "sessions.read",
            "metrics.read",
            "governance.read",
        ],
        PortalRole.ANALYST: [
            "sessions.read",
            "metrics.read",
            "governance.read",
        ],
        PortalRole.VIEWER: [
            "overview.read",
            "sessions.read",
            "metrics.read",
            "governance.read",
        ],
    }

    return list(actions_by_role[context.role])


def build_dashboard_router() -> APIRouter:
    """Build customer portal routes."""

    router = APIRouter(prefix="/api", tags=["dashboard"])

    @router.get("/me")
    async def get_me(
        context: TenantContext = Depends(require_tenant_context),
    ) -> dict[str, object]:
        """Return the authenticated user's dashboard tenant context."""

        return {
            "userId": context.user_id,
            "email": context.email,
            "organizationId": context.organization_id,
            "tenantId": context.tenant_id,
            "tenantName": context.tenant_name,
            "role": context.role.value,
            "subscriptionStatus": context.subscription_status.value,
            "hasActiveSubscription": context.has_active_subscription,
            "allowedActions": _allowed_actions(context),
        }

    return router
