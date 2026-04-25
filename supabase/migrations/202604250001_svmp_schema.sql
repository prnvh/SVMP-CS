create extension if not exists pgcrypto;

create table if not exists tenants (
    tenant_id text primary key,
    organization_id text,
    tenant_name text,
    website_url text,
    industry text,
    support_email text,
    billing_status text not null default 'none',
    billing_stripe_customer_id text,
    billing_stripe_subscription_id text,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists tenant_memberships (
    id text primary key default gen_random_uuid()::text,
    tenant_id text not null references tenants(tenant_id) on delete cascade,
    auth_provider text not null default 'supabase',
    provider_user_id text,
    email text,
    organization_id text,
    role text not null default 'viewer',
    permissions jsonb not null default '[]'::jsonb,
    status text not null default 'active',
    invited_at timestamptz,
    accepted_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists tenant_memberships_provider_user_unique
    on tenant_memberships (auth_provider, provider_user_id)
    where provider_user_id is not null;

create unique index if not exists tenant_memberships_email_unique
    on tenant_memberships (tenant_id, lower(email))
    where email is not null;

create table if not exists tenant_provider_identities (
    tenant_id text not null references tenants(tenant_id) on delete cascade,
    provider text not null,
    identity text not null,
    created_at timestamptz not null default timezone('utc', now()),
    primary key (provider, identity)
);

create index if not exists tenant_provider_identities_tenant_idx
    on tenant_provider_identities (tenant_id);

create table if not exists session_state (
    id text primary key default gen_random_uuid()::text,
    tenant_id text not null references tenants(tenant_id) on delete cascade,
    client_id text not null,
    user_id text not null,
    provider text,
    status text not null default 'open',
    processing boolean not null default false,
    processing_started_at timestamptz,
    context jsonb not null default '[]'::jsonb,
    messages jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    debounce_expires_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists session_state_open_identity_unique
    on session_state (tenant_id, client_id, user_id)
    where status = 'open';

create index if not exists session_state_tenant_updated_idx
    on session_state (tenant_id, updated_at desc);

create index if not exists session_state_ready_processing_idx
    on session_state (status, processing, debounce_expires_at, processing_started_at);

create table if not exists knowledge_base_entries (
    id text primary key default gen_random_uuid()::text,
    tenant_id text not null references tenants(tenant_id) on delete cascade,
    domain_id text not null,
    question text not null,
    answer text not null,
    tags jsonb not null default '[]'::jsonb,
    active boolean not null default true,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists knowledge_base_entries_tenant_updated_idx
    on knowledge_base_entries (tenant_id, updated_at desc);

create index if not exists knowledge_base_entries_domain_active_idx
    on knowledge_base_entries (tenant_id, domain_id, active);

create table if not exists governance_logs (
    id text primary key default gen_random_uuid()::text,
    tenant_id text not null references tenants(tenant_id) on delete cascade,
    client_id text not null,
    user_id text not null,
    decision text not null,
    similarity_score double precision,
    combined_text text not null,
    answer_supplied text,
    timestamp timestamptz not null default timezone('utc', now()),
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists governance_logs_tenant_timestamp_idx
    on governance_logs (tenant_id, timestamp desc);

create index if not exists governance_logs_tenant_decision_idx
    on governance_logs (tenant_id, decision);

create table if not exists integration_status (
    tenant_id text not null references tenants(tenant_id) on delete cascade,
    provider text not null,
    status text,
    health text,
    setup_warnings jsonb not null default '[]'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default timezone('utc', now()),
    primary key (tenant_id, provider)
);

create table if not exists audit_logs (
    id text primary key default gen_random_uuid()::text,
    tenant_id text not null references tenants(tenant_id) on delete cascade,
    actor_user_id text,
    actor_email text,
    action text not null,
    resource_type text not null,
    resource_id text not null,
    before_payload jsonb,
    after_payload jsonb,
    timestamp timestamptz not null default timezone('utc', now())
);

create index if not exists audit_logs_tenant_timestamp_idx
    on audit_logs (tenant_id, timestamp desc);

create table if not exists billing_subscriptions (
    tenant_id text primary key references tenants(tenant_id) on delete cascade,
    stripe_customer_id text,
    stripe_subscription_id text,
    status text not null default 'none',
    current_period_end timestamptz,
    price_id text,
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists billing_subscriptions_customer_unique
    on billing_subscriptions (stripe_customer_id)
    where stripe_customer_id is not null;

create unique index if not exists billing_subscriptions_subscription_unique
    on billing_subscriptions (stripe_subscription_id)
    where stripe_subscription_id is not null;

create table if not exists provider_events (
    provider text not null,
    event_id text not null,
    event_type text not null,
    tenant_id text references tenants(tenant_id) on delete set null,
    payload_hash text not null,
    created_at timestamptz not null default timezone('utc', now()),
    primary key (provider, event_id)
);
