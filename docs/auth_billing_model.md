# Auth And Billing Model

## Purpose

This document defines how users, organizations, tenants, roles, and subscriptions should work for the SVMP customer portal.

The main goal is tenant isolation. A signed-in user should only see data for the SVMP tenant connected to their authenticated organization.

## Identity Layers

SVMP uses four separate concepts:

```text
User             -> a human signing in through Clerk
Organization     -> the business account in Clerk
Tenant           -> the SVMP tenantId used in MongoDB
Subscription     -> Stripe billing state for the tenant
```

The important mapping is:

```text
Clerk organization id -> SVMP tenantId
```

The browser should not choose this mapping.

## Authentication

Users sign in through Clerk.

Required login methods:

- Google OAuth
- email fallback

The backend verifies Clerk-issued auth on every dashboard API request.

## Tenant Resolution

Every dashboard API request should resolve the tenant in this order:

1. Verify the user auth token.
2. Read the active Clerk organization from the session.
3. Look up the SVMP tenant mapped to that organization.
4. Load the user's membership and role for that tenant.
5. Load the tenant subscription status.
6. Continue only if role and subscription checks pass.

No dashboard API should accept trusted `tenantId` input from the browser.

## Roles

### Owner

Can manage:

- billing
- team
- integrations
- knowledge base
- brand voice
- settings
- sessions
- metrics
- governance

### Admin

Can manage:

- integrations
- knowledge base
- brand voice
- sessions
- metrics
- governance

Cannot manage:

- billing
- owner-level team controls

### Analyst

Can view:

- sessions
- governance
- metrics

Cannot edit:

- knowledge base
- brand voice
- integrations
- billing
- tenant settings

### Viewer

Can view read-only dashboard data.

Cannot edit tenant configuration or billing.

## Subscription Status

Subscription state comes from Stripe webhooks and is stored in MongoDB.

Recommended statuses:

```text
trialing
active
past_due
canceled
unpaid
incomplete
none
```

Operational portal access should require:

```text
trialing or active
```

When subscription is inactive, users should only see billing recovery screens and enough tenant context to understand what happened.

## Stripe Rules

Stripe Checkout and Billing Portal sessions are created by the backend.

Stripe webhooks are the source of truth for subscription activation.

Rules:

- verify webhook signatures
- store Stripe event ids in `provider_events`
- process events idempotently
- update `billing_subscriptions`
- mirror current billing status onto the tenant document only as a convenience
- do not activate access from a frontend success redirect alone

## Mongo Collections

### `tenant_memberships`

Purpose: connect Clerk users and organizations to SVMP tenants and roles.

Shape:

```json
{
  "tenantId": "stay",
  "clerkOrganizationId": "org_123",
  "clerkUserId": "user_123",
  "email": "owner@stayparfums.com",
  "role": "owner",
  "status": "active",
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

Indexes:

- unique `clerkOrganizationId`, `clerkUserId`
- `tenantId`, `role`

### `billing_subscriptions`

Purpose: store Stripe customer and subscription state by tenant.

Shape:

```json
{
  "tenantId": "stay",
  "stripeCustomerId": "cus_123",
  "stripeSubscriptionId": "sub_123",
  "status": "active",
  "currentPeriodEnd": "ISODate",
  "priceId": "price_123",
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

Indexes:

- unique `tenantId`
- `stripeCustomerId`
- `stripeSubscriptionId`

### `integration_status`

Purpose: show setup and health status for WhatsApp and future integrations.

Shape:

```json
{
  "tenantId": "stay",
  "provider": "whatsapp",
  "status": "connected",
  "health": "healthy",
  "lastInboundAt": "ISODate",
  "lastOutboundAt": "ISODate",
  "setupWarnings": [],
  "metadata": {},
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

Indexes:

- unique `tenantId`, `provider`

### `audit_logs`

Purpose: record administrative changes made in the dashboard.

Shape:

```json
{
  "tenantId": "stay",
  "actorUserId": "user_123",
  "actorEmail": "owner@stayparfums.com",
  "action": "knowledge_base.updated",
  "resourceType": "knowledge_base",
  "resourceId": "faq_123",
  "before": {},
  "after": {},
  "timestamp": "ISODate"
}
```

Indexes:

- `tenantId`, `timestamp`
- `tenantId`, `action`
- `tenantId`, `resourceType`, `resourceId`

### `provider_events`

Purpose: make provider webhooks idempotent.

Shape:

```json
{
  "provider": "stripe",
  "eventId": "evt_123",
  "eventType": "customer.subscription.updated",
  "tenantId": "stay",
  "processedAt": "ISODate",
  "payloadHash": "sha256..."
}
```

Indexes:

- unique `provider`, `eventId`
- `tenantId`, `processedAt`

## Tenant Document Extensions

The `tenants` document should eventually include:

```json
{
  "tenantId": "stay",
  "tenantName": "Stay Parfums",
  "websiteUrl": "https://stayparfums.com",
  "industry": "Fragrance",
  "supportEmail": "support@stayparfums.com",
  "brandVoice": {
    "tone": "Warm, polished, premium",
    "use": ["concise", "helpful", "confident"],
    "avoid": ["overpromising", "slang"],
    "escalationStyle": "Apologetic and clear"
  },
  "settings": {
    "confidenceThreshold": 0.75,
    "autoAnswerEnabled": true
  },
  "billing": {
    "status": "active",
    "stripeCustomerId": "cus_123",
    "stripeSubscriptionId": "sub_123"
  },
  "onboarding": {
    "status": "completed",
    "steps": {
      "profile": true,
      "brandVoice": true,
      "knowledgeBase": true,
      "whatsapp": true,
      "testConversation": true
    }
  }
}
```

The canonical billing state should still live in `billing_subscriptions`; the tenant-level billing object is a fast dashboard summary.

## Backend Dependencies

Dashboard routes should eventually use dependencies like:

```python
require_user()
require_tenant_context()
require_role(["owner", "admin"])
require_active_subscription()
```

The route handler should receive an already-resolved context and should not parse auth or tenant ownership manually.

## Production Requirements

Before paid users rely on the portal:

- verify Clerk auth on every dashboard API
- enforce role permissions on the backend
- enforce subscription status on the backend
- scope every query by resolved tenant
- write audit logs for KB, brand voice, settings, integrations, and billing-sensitive changes
- handle Stripe webhooks idempotently
- handle provider webhooks idempotently
- avoid storing provider credentials in plain text
- add error states, loading states, and empty states in the UI
- add monitoring and structured logging
