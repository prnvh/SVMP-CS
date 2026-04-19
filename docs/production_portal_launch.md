# Production Portal Launch

## Goal

The customer portal should be private by default. A user must sign in through Clerk, belong to the correct Clerk organization, map to one SVMP tenant in MongoDB, and pass backend role/subscription checks before any tenant data is returned.

## Frontend Env

Set these in Vercel for the customer portal:

```text
NEXT_PUBLIC_PORTAL_AUTH_MODE=clerk
NEXT_PUBLIC_API_BASE_URL=https://api.svmpsystems.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
CLERK_JWT_TEMPLATE=svmp-dashboard
NEXT_PUBLIC_CLERK_JWT_TEMPLATE=svmp-dashboard
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/login
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/signup
```

Do not enable preview auth for paid-client production access:

```text
PORTAL_ALLOW_UNSAFE_PREVIEW_AUTH=false
```

## Backend Env

Set these on the FastAPI host:

```text
APP_ENV=production
DASHBOARD_AUTH_MODE=clerk
DASHBOARD_APP_URL=https://app.svmpsystems.com
DASHBOARD_CORS_ORIGINS=https://svmp-cs.vercel.app,https://app.svmpsystems.com
CLERK_ISSUER=https://your-clerk-issuer
CLERK_JWKS_URL=https://your-clerk-issuer/.well-known/jwks.json
CLERK_AUDIENCE=svmp-dashboard
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

Keep the existing MongoDB, OpenAI, and WhatsApp provider secrets configured too.

## Access Setup

1. Create the tenant document in MongoDB.
2. Create the Clerk organization.
3. Invite the user in Clerk.
4. Copy the Clerk organization id and user id.
5. Seed the backend membership:

```powershell
& .\.venv\Scripts\python.exe .\scripts\seed_portal_access.py `
  --tenant-id stay `
  --clerk-organization-id org_... `
  --clerk-user-id user_... `
  --email prnvvh@gmail.com `
  --role owner `
  --subscription-status active
```

The browser never sends or chooses `tenantId`. The backend resolves it from `tenant_memberships`.

## Sanity Checks

- Incognito `/dashboard` redirects to `/login`.
- Login works inside `/login`, not by directly opening a public dashboard.
- `/api/me` returns exactly one tenant context.
- Dashboard API requests include a Clerk bearer token.
- FastAPI rejects dashboard API requests without auth.
- Operational APIs return `402` when subscription status is not `active` or `trialing`.
- KB, brand voice, settings, and WhatsApp edits create audit logs.
