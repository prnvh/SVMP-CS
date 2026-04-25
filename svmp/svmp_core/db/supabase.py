"""Supabase/Postgres-backed persistence adapters for SVMP."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from svmp_core.config import Settings, get_settings
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
from svmp_core.exceptions import DatabaseError
from svmp_core.models import GovernanceLog, KnowledgeEntry, SessionState


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _normalize_database_url(database_url: str) -> str:
    """Normalize common Postgres URLs to SQLAlchemy's psycopg dialect."""

    normalized = database_url.strip()
    if normalized.startswith("postgresql+psycopg://"):
        return normalized
    if normalized.startswith("postgresql://"):
        return normalized.replace("postgresql://", "postgresql+psycopg://", 1)
    if normalized.startswith("postgres://"):
        return normalized.replace("postgres://", "postgresql+psycopg://", 1)
    return normalized


def _row_mapping(row: Any) -> dict[str, Any] | None:
    """Return a plain mapping from a SQLAlchemy row when present."""

    if row is None:
        return None
    return dict(row._mapping)


async def _fetchone(
    connection: AsyncConnection,
    sql: str,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Execute a query and return the first row as a mapping."""

    result = await connection.execute(text(sql), params or {})
    return _row_mapping(result.first())


async def _fetchall(
    connection: AsyncConnection,
    sql: str,
    params: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute a query and return all rows as plain mappings."""

    result = await connection.execute(text(sql), params or {})
    return [dict(row._mapping) for row in result.fetchall()]


def _message_payloads(messages: Sequence[Any]) -> list[dict[str, Any]]:
    """Serialize session messages for JSONB storage."""

    payloads: list[dict[str, Any]] = []
    for message in messages:
        if hasattr(message, "model_dump"):
            payload = message.model_dump(by_alias=True, exclude_none=True)
        elif isinstance(message, Mapping):
            payload = dict(message)
        else:
            continue
        payloads.append(payload)
    return payloads


def _jsonb(value: Any) -> str:
    """Serialize a Python value for JSONB bind parameters."""

    return json.dumps(value, ensure_ascii=True, default=str)


def _session_row_to_model(row: Mapping[str, Any] | None) -> SessionState | None:
    """Convert a session row into the public Pydantic model."""

    if row is None:
        return None

    return SessionState.model_validate(
        {
            "id": row.get("id"),
            "tenantId": row.get("tenant_id"),
            "clientId": row.get("client_id"),
            "userId": row.get("user_id"),
            "provider": row.get("provider"),
            "status": row.get("status"),
            "processing": row.get("processing"),
            "context": list(row.get("context") or []),
            "messages": list(row.get("messages") or []),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
            "debounceExpiresAt": row.get("debounce_expires_at"),
        }
    )


def _knowledge_row_to_model(row: Mapping[str, Any] | None) -> KnowledgeEntry | None:
    """Convert a knowledge-base row into the public Pydantic model."""

    if row is None:
        return None

    return KnowledgeEntry.model_validate(
        {
            "id": row.get("id"),
            "tenantId": row.get("tenant_id"),
            "domainId": row.get("domain_id"),
            "question": row.get("question"),
            "answer": row.get("answer"),
            "tags": list(row.get("tags") or []),
            "active": row.get("active"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }
    )


def _governance_row_to_model(row: Mapping[str, Any] | None) -> GovernanceLog | None:
    """Convert a governance-log row into the public Pydantic model."""

    if row is None:
        return None

    return GovernanceLog.model_validate(
        {
            "id": row.get("id"),
            "tenantId": row.get("tenant_id"),
            "clientId": row.get("client_id"),
            "userId": row.get("user_id"),
            "decision": row.get("decision"),
            "similarityScore": row.get("similarity_score"),
            "combinedText": row.get("combined_text"),
            "answerSupplied": row.get("answer_supplied"),
            "timestamp": row.get("timestamp"),
            "metadata": dict(row.get("metadata") or {}),
        }
    )


def _tenant_row_to_document(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Convert a tenant row into the document shape used across the app."""

    if row is None:
        return None

    payload = deepcopy(row.get("payload") or {})
    if not isinstance(payload, dict):
        payload = {}

    payload["tenantId"] = row.get("tenant_id")
    payload["organizationId"] = row.get("organization_id")
    payload["tenantName"] = row.get("tenant_name")
    payload["websiteUrl"] = row.get("website_url")
    payload["industry"] = row.get("industry")
    payload["supportEmail"] = row.get("support_email")
    payload["createdAt"] = row.get("created_at")
    payload["updatedAt"] = row.get("updated_at")

    billing = payload.get("billing")
    if not isinstance(billing, dict):
        billing = {}
    billing["status"] = row.get("billing_status") or billing.get("status") or "none"
    billing["stripeCustomerId"] = row.get("billing_stripe_customer_id")
    billing["stripeSubscriptionId"] = row.get("billing_stripe_subscription_id")
    payload["billing"] = billing

    return payload


def _prepare_tenant_document(tenant_document: Mapping[str, Any]) -> dict[str, Any]:
    """Split a public tenant document into normalized relational columns + payload."""

    payload = deepcopy(dict(tenant_document))
    tenant_id = payload.get("tenantId")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise DatabaseError("tenant document missing tenantId")

    organization_id = payload.get("organizationId")
    tenant_name = payload.get("tenantName")
    website_url = payload.get("websiteUrl")
    industry = payload.get("industry")
    support_email = payload.get("supportEmail")
    created_at = payload.get("createdAt") if isinstance(payload.get("createdAt"), datetime) else _utcnow()
    updated_at = payload.get("updatedAt") if isinstance(payload.get("updatedAt"), datetime) else _utcnow()

    billing = payload.get("billing")
    billing_mapping = dict(billing) if isinstance(billing, Mapping) else {}

    for key in (
        "tenantId",
        "organizationId",
        "tenantName",
        "websiteUrl",
        "industry",
        "supportEmail",
        "createdAt",
        "updatedAt",
    ):
        payload.pop(key, None)

    payload["billing"] = {
        **billing_mapping,
        "status": billing_mapping.get("status") or "none",
        "stripeCustomerId": billing_mapping.get("stripeCustomerId"),
        "stripeSubscriptionId": billing_mapping.get("stripeSubscriptionId"),
    }

    return {
        "tenant_id": tenant_id.strip(),
        "organization_id": organization_id.strip() if isinstance(organization_id, str) and organization_id.strip() else None,
        "tenant_name": tenant_name.strip() if isinstance(tenant_name, str) and tenant_name.strip() else None,
        "website_url": website_url.strip() if isinstance(website_url, str) and website_url.strip() else None,
        "industry": industry.strip() if isinstance(industry, str) and industry.strip() else None,
        "support_email": support_email.strip() if isinstance(support_email, str) and support_email.strip() else None,
        "billing_status": str(payload["billing"].get("status") or "none").strip() or "none",
        "billing_stripe_customer_id": payload["billing"].get("stripeCustomerId"),
        "billing_stripe_subscription_id": payload["billing"].get("stripeSubscriptionId"),
        "payload": payload,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _apply_nested_patch(target: dict[str, Any], key: str, value: Any) -> None:
    """Apply a dotted-path patch into a nested document."""

    segments = [segment for segment in key.split(".") if segment]
    if not segments:
        return

    current: dict[str, Any] = target
    for segment in segments[:-1]:
        existing = current.get(segment)
        if not isinstance(existing, dict):
            existing = {}
            current[segment] = existing
        current = existing

    current[segments[-1]] = value


def _extract_provider_identities(tenant_document: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Extract normalized provider routing identities from a tenant document."""

    channels = tenant_document.get("channels")
    if not isinstance(channels, Mapping):
        return []

    extracted: list[tuple[str, str]] = []

    meta = channels.get("meta")
    if isinstance(meta, Mapping):
        for key in ("phoneNumberIds", "displayNumbers"):
            values = meta.get(key)
            if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
                for value in values:
                    if isinstance(value, str) and value.strip():
                        extracted.append(("meta", value.strip()))

    twilio = channels.get("twilio")
    if isinstance(twilio, Mapping):
        for key in ("whatsappNumbers", "accountSids"):
            values = twilio.get(key)
            if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
                for value in values:
                    if isinstance(value, str) and value.strip():
                        extracted.append(("twilio", value.strip()))

    deduplicated: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for provider, identity in extracted:
        item = (provider, identity)
        if item in seen:
            continue
        seen.add(item)
        deduplicated.append(item)
    return deduplicated


def _normalize_session_update(data: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize session update keys into storage columns."""

    field_map = {
        "provider": "provider",
        "status": "status",
        "processing": "processing",
        "context": "context",
        "messages": "messages",
        "createdAt": "created_at",
        "created_at": "created_at",
        "updatedAt": "updated_at",
        "updated_at": "updated_at",
        "debounceExpiresAt": "debounce_expires_at",
        "debounce_expires_at": "debounce_expires_at",
        "processingStartedAt": "processing_started_at",
        "processing_started_at": "processing_started_at",
    }

    normalized: dict[str, Any] = {}
    for key, value in data.items():
        column = field_map.get(key)
        if column is None:
            continue
        if column == "messages" and isinstance(value, Sequence):
            normalized[column] = _jsonb(_message_payloads(value))
            continue
        if column == "context" and isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            normalized[column] = _jsonb([str(item) for item in value])
            continue
        normalized[column] = value

    if "updated_at" not in normalized:
        normalized["updated_at"] = _utcnow()

    if "processing" in normalized and "processing_started_at" not in normalized:
        normalized["processing_started_at"] = _utcnow() if normalized["processing"] else None

    return normalized


def _normalize_knowledge_update(data: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize knowledge-base update keys into storage columns."""

    field_map = {
        "domainId": "domain_id",
        "domain_id": "domain_id",
        "question": "question",
        "answer": "answer",
        "tags": "tags",
        "active": "active",
        "createdAt": "created_at",
        "created_at": "created_at",
        "updatedAt": "updated_at",
        "updated_at": "updated_at",
    }

    normalized: dict[str, Any] = {}
    for key, value in data.items():
        column = field_map.get(key)
        if column is None:
            continue
        if column == "tags" and isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            normalized[column] = _jsonb([str(item) for item in value])
            continue
        normalized[column] = value

    if "updated_at" not in normalized:
        normalized["updated_at"] = _utcnow()

    return normalized


async def _replace_provider_identities(
    connection: AsyncConnection,
    tenant_id: str,
    tenant_document: Mapping[str, Any],
) -> None:
    """Refresh provider routing identities for a tenant."""

    await connection.execute(
        text("DELETE FROM tenant_provider_identities WHERE tenant_id = :tenant_id"),
        {"tenant_id": tenant_id},
    )

    identities = _extract_provider_identities(tenant_document)
    for provider, identity in identities:
        await connection.execute(
            text(
                """
                INSERT INTO tenant_provider_identities (
                    tenant_id,
                    provider,
                    identity,
                    created_at
                ) VALUES (
                    :tenant_id,
                    :provider,
                    :identity,
                    :created_at
                )
                ON CONFLICT (provider, identity) DO UPDATE
                SET tenant_id = EXCLUDED.tenant_id
                """
            ),
            {
                "tenant_id": tenant_id,
                "provider": provider,
                "identity": identity,
                "created_at": _utcnow(),
            },
        )


async def _upsert_tenant_document(
    connection: AsyncConnection,
    tenant_document: Mapping[str, Any],
) -> dict[str, Any]:
    """Insert or update a tenant row and return the stored document."""

    prepared = _prepare_tenant_document(tenant_document)
    row = await _fetchone(
        connection,
        """
        INSERT INTO tenants (
            tenant_id,
            organization_id,
            tenant_name,
            website_url,
            industry,
            support_email,
            billing_status,
            billing_stripe_customer_id,
            billing_stripe_subscription_id,
            payload,
            created_at,
            updated_at
        ) VALUES (
            :tenant_id,
            :organization_id,
            :tenant_name,
            :website_url,
            :industry,
            :support_email,
            :billing_status,
            :billing_stripe_customer_id,
            :billing_stripe_subscription_id,
            CAST(:payload AS jsonb),
            :created_at,
            :updated_at
        )
        ON CONFLICT (tenant_id) DO UPDATE
        SET
            organization_id = EXCLUDED.organization_id,
            tenant_name = EXCLUDED.tenant_name,
            website_url = EXCLUDED.website_url,
            industry = EXCLUDED.industry,
            support_email = EXCLUDED.support_email,
            billing_status = EXCLUDED.billing_status,
            billing_stripe_customer_id = EXCLUDED.billing_stripe_customer_id,
            billing_stripe_subscription_id = EXCLUDED.billing_stripe_subscription_id,
            payload = EXCLUDED.payload,
            updated_at = EXCLUDED.updated_at
        RETURNING *
        """,
        {
            **prepared,
            "payload": _jsonb(prepared["payload"]),
        },
    )
    if row is None:
        raise DatabaseError("failed to persist tenant document")

    await _replace_provider_identities(connection, prepared["tenant_id"], tenant_document)
    stored = _tenant_row_to_document(row)
    if stored is None:
        raise DatabaseError("failed to load tenant document")
    return stored


class _RepositoryBase:
    """Shared helpers for concrete repositories."""

    def __init__(self, database: "SupabaseDatabase") -> None:
        self._database = database

    @property
    def _engine(self) -> AsyncEngine:
        engine = self._database._engine
        if engine is None:
            raise DatabaseError("database not connected")
        return engine


class SupabaseSessionStateRepository(_RepositoryBase, SessionStateRepository):
    """Postgres-backed repository for active session state."""

    async def get_by_identity(
        self,
        tenant_id: str,
        client_id: str,
        user_id: str,
    ) -> SessionState | None:
        async with self._engine.connect() as connection:
            row = await _fetchone(
                connection,
                """
                SELECT *
                FROM session_state
                WHERE tenant_id = :tenant_id
                  AND client_id = :client_id
                  AND user_id = :user_id
                  AND status = 'open'
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                {
                    "tenant_id": tenant_id,
                    "client_id": client_id,
                    "user_id": user_id,
                },
            )
        return _session_row_to_model(row)

    async def create(self, session: SessionState) -> SessionState:
        session_id = session.id or str(uuid4())
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                INSERT INTO session_state (
                    id,
                    tenant_id,
                    client_id,
                    user_id,
                    provider,
                    status,
                    processing,
                    processing_started_at,
                    context,
                    messages,
                    created_at,
                    updated_at,
                    debounce_expires_at
                ) VALUES (
                    :id,
                    :tenant_id,
                    :client_id,
                    :user_id,
                    :provider,
                    :status,
                    :processing,
                    :processing_started_at,
                    CAST(:context AS jsonb),
                    CAST(:messages AS jsonb),
                    :created_at,
                    :updated_at,
                    :debounce_expires_at
                )
                RETURNING *
                """,
                {
                    "id": session_id,
                    "tenant_id": session.tenant_id,
                    "client_id": session.client_id,
                    "user_id": session.user_id,
                    "provider": session.provider,
                    "status": session.status,
                    "processing": session.processing,
                    "processing_started_at": _utcnow() if session.processing else None,
                    "context": _jsonb(list(session.context)),
                    "messages": _jsonb(_message_payloads(session.messages)),
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "debounce_expires_at": session.debounce_expires_at,
                },
            )
        model = _session_row_to_model(row)
        if model is None:
            raise DatabaseError("failed to create session")
        return model

    async def update_by_id(
        self,
        session_id: str,
        data: Mapping[str, Any],
    ) -> SessionState | None:
        updates = _normalize_session_update(data)
        if not updates:
            return None

        set_clauses = ", ".join(
            f"{column} = CAST(:{column} AS jsonb)"
            if column in {"context", "messages"}
            else f"{column} = :{column}"
            for column in updates
        )
        params = {"id": session_id, **updates}

        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                f"""
                UPDATE session_state
                SET {set_clauses}
                WHERE id = :id
                RETURNING *
                """,
                params,
            )
        return _session_row_to_model(row)

    async def acquire_ready_session(self, now: datetime) -> SessionState | None:
        lock_cutoff = now - timedelta(
            seconds=self._database._settings.WORKFLOW_B_PROCESSING_LOCK_TIMEOUT_SECONDS
        )
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                WITH candidate AS (
                    SELECT id
                    FROM session_state
                    WHERE status = 'open'
                      AND debounce_expires_at <= :now
                      AND (
                        processing = FALSE
                        OR (
                            processing_started_at IS NOT NULL
                            AND processing_started_at <= :lock_cutoff
                        )
                      )
                    ORDER BY debounce_expires_at ASC, updated_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE session_state AS session
                SET
                    processing = TRUE,
                    processing_started_at = :now,
                    updated_at = GREATEST(session.updated_at, :now)
                FROM candidate
                WHERE session.id = candidate.id
                RETURNING session.*
                """,
                {"now": now, "lock_cutoff": lock_cutoff},
            )
        return _session_row_to_model(row)

    async def acquire_ready_session_by_id(
        self,
        session_id: str,
        now: datetime,
    ) -> SessionState | None:
        lock_cutoff = now - timedelta(
            seconds=self._database._settings.WORKFLOW_B_PROCESSING_LOCK_TIMEOUT_SECONDS
        )
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                WITH candidate AS (
                    SELECT id
                    FROM session_state
                    WHERE id = :id
                      AND status = 'open'
                      AND debounce_expires_at <= :now
                      AND (
                        processing = FALSE
                        OR (
                            processing_started_at IS NOT NULL
                            AND processing_started_at <= :lock_cutoff
                        )
                      )
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE session_state AS session
                SET
                    processing = TRUE,
                    processing_started_at = :now,
                    updated_at = GREATEST(session.updated_at, :now)
                FROM candidate
                WHERE session.id = candidate.id
                RETURNING session.*
                """,
                {"id": session_id, "now": now, "lock_cutoff": lock_cutoff},
            )
        return _session_row_to_model(row)

    async def delete_stale_sessions(self, before: datetime) -> int:
        async with self._engine.begin() as connection:
            result = await connection.execute(
                text("DELETE FROM session_state WHERE updated_at < :before"),
                {"before": before},
            )
        return int(result.rowcount or 0)

    async def list_stale_sessions(self, before: datetime) -> list[SessionState]:
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                """
                SELECT *
                FROM session_state
                WHERE updated_at < :before
                ORDER BY updated_at ASC
                LIMIT 250
                """,
                {"before": before},
            )
        return [model for row in rows if (model := _session_row_to_model(row)) is not None]

    async def list_by_tenant(
        self,
        tenant_id: str,
        *,
        limit: int = 50,
    ) -> list[SessionState]:
        bounded_limit = max(1, min(limit, 100))
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                """
                SELECT *
                FROM session_state
                WHERE tenant_id = :tenant_id
                ORDER BY updated_at DESC
                LIMIT :limit
                """,
                {"tenant_id": tenant_id, "limit": bounded_limit},
            )
        return [model for row in rows if (model := _session_row_to_model(row)) is not None]

    async def get_by_id(
        self,
        tenant_id: str,
        session_id: str,
    ) -> SessionState | None:
        async with self._engine.connect() as connection:
            row = await _fetchone(
                connection,
                """
                SELECT *
                FROM session_state
                WHERE id = :id
                  AND tenant_id = :tenant_id
                LIMIT 1
                """,
                {"id": session_id, "tenant_id": tenant_id},
            )
        return _session_row_to_model(row)


class SupabaseKnowledgeBaseRepository(_RepositoryBase, KnowledgeBaseRepository):
    """Postgres-backed repository for tenant-scoped FAQ entries."""

    async def list_active_by_tenant_and_domain(
        self,
        tenant_id: str,
        domain_id: str,
    ) -> list[KnowledgeEntry]:
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                """
                SELECT *
                FROM knowledge_base_entries
                WHERE domain_id = :domain_id
                  AND active = TRUE
                  AND (
                    tenant_id = :tenant_id
                    OR tenant_id = :shared_tenant_id
                  )
                ORDER BY
                    CASE WHEN tenant_id = :shared_tenant_id THEN 1 ELSE 0 END ASC,
                    question ASC
                """,
                {
                    "tenant_id": tenant_id,
                    "shared_tenant_id": self._database._settings.SHARED_KB_TENANT_ID,
                    "domain_id": domain_id,
                },
            )
        return [model for row in rows if (model := _knowledge_row_to_model(row)) is not None]

    async def list_by_tenant(
        self,
        tenant_id: str,
        *,
        active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[KnowledgeEntry]:
        clauses = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {"tenant_id": tenant_id, "limit": max(1, min(limit, 250))}
        if active is not None:
            clauses.append("active = :active")
            params["active"] = active
        normalized_search = search.strip() if isinstance(search, str) else ""
        if normalized_search:
            params["search"] = f"%{normalized_search}%"
            clauses.append(
                "("
                "question ILIKE :search "
                "OR answer ILIKE :search "
                "OR domain_id ILIKE :search "
                "OR CAST(tags AS text) ILIKE :search"
                ")"
            )

        where_sql = " AND ".join(clauses)
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                f"""
                SELECT *
                FROM knowledge_base_entries
                WHERE {where_sql}
                ORDER BY updated_at DESC
                LIMIT :limit
                """,
                params,
            )
        return [model for row in rows if (model := _knowledge_row_to_model(row)) is not None]

    async def create(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        entry_id = entry.id or str(uuid4())
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                INSERT INTO knowledge_base_entries (
                    id,
                    tenant_id,
                    domain_id,
                    question,
                    answer,
                    tags,
                    active,
                    created_at,
                    updated_at
                ) VALUES (
                    :id,
                    :tenant_id,
                    :domain_id,
                    :question,
                    :answer,
                    CAST(:tags AS jsonb),
                    :active,
                    :created_at,
                    :updated_at
                )
                RETURNING *
                """,
                {
                    "id": entry_id,
                    "tenant_id": entry.tenant_id,
                    "domain_id": entry.domain_id,
                    "question": entry.question,
                    "answer": entry.answer,
                    "tags": _jsonb(list(entry.tags)),
                    "active": entry.active,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at,
                },
            )
        model = _knowledge_row_to_model(row)
        if model is None:
            raise DatabaseError("failed to create knowledge-base entry")
        return model

    async def replace_entries_for_tenant_domain(
        self,
        tenant_id: str,
        domain_id: str,
        entries: Sequence[KnowledgeEntry],
    ) -> int:
        async with self._engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    DELETE FROM knowledge_base_entries
                    WHERE tenant_id = :tenant_id
                      AND domain_id = :domain_id
                    """
                ),
                {"tenant_id": tenant_id, "domain_id": domain_id},
            )
            written = 0
            for entry in entries:
                row = await _fetchone(
                    connection,
                    """
                    INSERT INTO knowledge_base_entries (
                        id,
                        tenant_id,
                        domain_id,
                        question,
                        answer,
                        tags,
                        active,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :tenant_id,
                        :domain_id,
                        :question,
                        :answer,
                        CAST(:tags AS jsonb),
                        :active,
                        :created_at,
                        :updated_at
                    )
                    RETURNING id
                    """,
                    {
                        "id": entry.id or str(uuid4()),
                        "tenant_id": entry.tenant_id,
                        "domain_id": entry.domain_id,
                        "question": entry.question,
                        "answer": entry.answer,
                        "tags": _jsonb(list(entry.tags)),
                        "active": entry.active,
                        "created_at": entry.created_at,
                        "updated_at": entry.updated_at,
                    },
                )
                if row is not None and row.get("id") is not None:
                    written += 1
        return written

    async def update_by_id(
        self,
        tenant_id: str,
        entry_id: str,
        data: Mapping[str, Any],
    ) -> KnowledgeEntry | None:
        updates = _normalize_knowledge_update(data)
        if not updates:
            return None

        set_clauses = ", ".join(
            f"{column} = CAST(:{column} AS jsonb)"
            if column == "tags"
            else f"{column} = :{column}"
            for column in updates
        )
        params = {"tenant_id": tenant_id, "id": entry_id, **updates}

        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                f"""
                UPDATE knowledge_base_entries
                SET {set_clauses}
                WHERE tenant_id = :tenant_id
                  AND id = :id
                RETURNING *
                """,
                params,
            )
        return _knowledge_row_to_model(row)

    async def deactivate_by_id(
        self,
        tenant_id: str,
        entry_id: str,
        data: Mapping[str, Any],
    ) -> KnowledgeEntry | None:
        return await self.update_by_id(
            tenant_id,
            entry_id,
            {"active": False, **dict(data)},
        )


class SupabaseGovernanceLogRepository(_RepositoryBase, GovernanceLogRepository):
    """Postgres-backed repository for immutable governance logs."""

    async def create(self, log: GovernanceLog) -> GovernanceLog:
        log_id = log.id or str(uuid4())
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                INSERT INTO governance_logs (
                    id,
                    tenant_id,
                    client_id,
                    user_id,
                    decision,
                    similarity_score,
                    combined_text,
                    answer_supplied,
                    timestamp,
                    metadata
                ) VALUES (
                    :id,
                    :tenant_id,
                    :client_id,
                    :user_id,
                    :decision,
                    :similarity_score,
                    :combined_text,
                    :answer_supplied,
                    :timestamp,
                    CAST(:metadata AS jsonb)
                )
                RETURNING *
                """,
                {
                    "id": log_id,
                    "tenant_id": log.tenant_id,
                    "client_id": log.client_id,
                    "user_id": log.user_id,
                    "decision": log.decision.value,
                    "similarity_score": log.similarity_score,
                    "combined_text": log.combined_text,
                    "answer_supplied": log.answer_supplied,
                    "timestamp": log.timestamp,
                    "metadata": _jsonb(dict(log.metadata)),
                },
            )
        model = _governance_row_to_model(row)
        if model is None:
            raise DatabaseError("failed to create governance log")
        return model

    async def list_by_tenant(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
    ) -> list[GovernanceLog]:
        bounded_limit = max(1, min(limit, 250))
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                """
                SELECT *
                FROM governance_logs
                WHERE tenant_id = :tenant_id
                ORDER BY timestamp DESC
                LIMIT :limit
                """,
                {"tenant_id": tenant_id, "limit": bounded_limit},
            )
        return [model for row in rows if (model := _governance_row_to_model(row)) is not None]

    async def count_by_decision(self, tenant_id: str) -> Mapping[str, int]:
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                """
                SELECT decision, COUNT(*) AS count
                FROM governance_logs
                WHERE tenant_id = :tenant_id
                GROUP BY decision
                """,
                {"tenant_id": tenant_id},
            )
        return {
            str(row["decision"]): int(row["count"])
            for row in rows
            if row.get("decision") is not None
        }


class SupabaseTenantRepository(_RepositoryBase, TenantRepository):
    """Postgres-backed repository for tenant metadata and access control."""

    async def get_by_tenant_id(self, tenant_id: str) -> Mapping[str, Any] | None:
        async with self._engine.connect() as connection:
            row = await _fetchone(
                connection,
                """
                SELECT *
                FROM tenants
                WHERE tenant_id = :tenant_id
                LIMIT 1
                """,
                {"tenant_id": tenant_id},
            )
        return _tenant_row_to_document(row)

    async def update_by_tenant_id(
        self,
        tenant_id: str,
        data: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                SELECT *
                FROM tenants
                WHERE tenant_id = :tenant_id
                FOR UPDATE
                """,
                {"tenant_id": tenant_id},
            )
            if row is None:
                return None

            document = _tenant_row_to_document(row) or {"tenantId": tenant_id}
            for key, value in dict(data).items():
                _apply_nested_patch(document, key, value)
            document["tenantId"] = tenant_id
            document["updatedAt"] = _utcnow()

            return await _upsert_tenant_document(connection, document)

    async def upsert_tenant(self, tenant_document: Mapping[str, Any]) -> Mapping[str, Any]:
        async with self._engine.begin() as connection:
            return await _upsert_tenant_document(connection, tenant_document)

    async def resolve_tenant_id_for_provider(
        self,
        *,
        provider: str,
        identities: Sequence[str],
    ) -> str | None:
        normalized_provider = provider.strip().lower()
        normalized_identities = [
            identity.strip()
            for identity in identities
            if isinstance(identity, str) and identity.strip()
        ]
        if not normalized_provider or not normalized_identities:
            return None

        placeholders = ", ".join(f":identity_{index}" for index in range(len(normalized_identities)))
        params = {
            "provider": normalized_provider,
            **{f"identity_{index}": value for index, value in enumerate(normalized_identities)},
        }
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                f"""
                SELECT DISTINCT tenant_id
                FROM tenant_provider_identities
                WHERE provider = :provider
                  AND identity IN ({placeholders})
                LIMIT 2
                """,
                params,
            )

        tenant_ids = {
            str(row["tenant_id"]).strip()
            for row in rows
            if isinstance(row.get("tenant_id"), str) and row["tenant_id"].strip()
        }
        if not tenant_ids:
            return None
        if len(tenant_ids) > 1:
            raise DatabaseError("tenant resolution is ambiguous for provider payload")
        return next(iter(tenant_ids))

    async def resolve_dashboard_tenant_context(
        self,
        *,
        auth_provider: str = "supabase",
        provider_user_id: str | None = None,
        email: str | None = None,
        organization_id: str | None = None,
    ) -> Mapping[str, Any] | None:
        normalized_provider = auth_provider.strip().lower() if auth_provider.strip() else "supabase"
        normalized_user_id = provider_user_id.strip() if isinstance(provider_user_id, str) and provider_user_id.strip() else ""
        normalized_email = email.strip().lower() if isinstance(email, str) and email.strip() else ""
        if not normalized_user_id and not normalized_email:
            return None

        async with self._engine.begin() as connection:
            membership = None
            if normalized_user_id:
                membership = await _fetchone(
                    connection,
                    """
                    SELECT *
                    FROM tenant_memberships
                    WHERE auth_provider = :auth_provider
                      AND provider_user_id = :provider_user_id
                      AND status = 'active'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    {
                        "auth_provider": normalized_provider,
                        "provider_user_id": normalized_user_id,
                    },
                )

            if membership is None and normalized_email:
                membership = await _fetchone(
                    connection,
                    """
                    SELECT *
                    FROM tenant_memberships
                    WHERE lower(email) = :email
                      AND status IN ('active', 'invited')
                    ORDER BY
                        CASE WHEN status = 'active' THEN 0 ELSE 1 END ASC,
                        updated_at DESC
                    LIMIT 1
                    """,
                    {"email": normalized_email},
                )

                if (
                    membership is not None
                    and membership.get("status") == "invited"
                    and normalized_user_id
                ):
                    membership = await _fetchone(
                        connection,
                        """
                        UPDATE tenant_memberships
                        SET
                            auth_provider = :auth_provider,
                            provider_user_id = :provider_user_id,
                            status = 'active',
                            accepted_at = :accepted_at,
                            updated_at = :updated_at
                        WHERE id = :id
                        RETURNING *
                        """,
                        {
                            "id": membership["id"],
                            "auth_provider": normalized_provider,
                            "provider_user_id": normalized_user_id,
                            "accepted_at": _utcnow(),
                            "updated_at": _utcnow(),
                        },
                    )

            if membership is None:
                return None

            tenant_id = membership.get("tenant_id")
            if not isinstance(tenant_id, str) or not tenant_id.strip():
                return None

            tenant_row = await _fetchone(
                connection,
                """
                SELECT *
                FROM tenants
                WHERE tenant_id = :tenant_id
                LIMIT 1
                """,
                {"tenant_id": tenant_id},
            )
            tenant_document = _tenant_row_to_document(tenant_row) or {}
            billing = tenant_document.get("billing")
            billing_mapping = dict(billing) if isinstance(billing, Mapping) else {}

            return {
                "tenantId": tenant_id,
                "tenantName": tenant_document.get("tenantName"),
                "role": membership.get("role") or "viewer",
                "email": membership.get("email") or normalized_email or None,
                "organizationId": membership.get("organization_id") or organization_id or tenant_document.get("organizationId") or tenant_id,
                "permissions": list(membership.get("permissions") or []),
                "subscriptionStatus": billing_mapping.get("status") or "none",
                "billing": billing_mapping,
            }

    async def list_integration_status(
        self,
        tenant_id: str,
    ) -> list[Mapping[str, Any]]:
        async with self._engine.connect() as connection:
            rows = await _fetchall(
                connection,
                """
                SELECT *
                FROM integration_status
                WHERE tenant_id = :tenant_id
                ORDER BY provider ASC
                """,
                {"tenant_id": tenant_id},
            )
        return [
            {
                "tenantId": row.get("tenant_id"),
                "provider": row.get("provider"),
                "status": row.get("status"),
                "health": row.get("health"),
                "setupWarnings": list(row.get("setup_warnings") or []),
                "metadata": dict(row.get("metadata") or {}),
                "updatedAt": row.get("updated_at"),
            }
            for row in rows
        ]

    async def update_integration_status(
        self,
        tenant_id: str,
        provider: str,
        data: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        payload = dict(data)
        status_value = payload.get("status")
        health = payload.get("health")
        setup_warnings = payload.get("setupWarnings") if "setupWarnings" in payload else payload.get("setup_warnings")
        metadata = payload.get("metadata")

        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                INSERT INTO integration_status (
                    tenant_id,
                    provider,
                    status,
                    health,
                    setup_warnings,
                    metadata,
                    updated_at
                ) VALUES (
                    :tenant_id,
                    :provider,
                    :status,
                    :health,
                    CAST(:setup_warnings AS jsonb),
                    CAST(:metadata AS jsonb),
                    :updated_at
                )
                ON CONFLICT (tenant_id, provider) DO UPDATE
                SET
                    status = COALESCE(EXCLUDED.status, integration_status.status),
                    health = COALESCE(EXCLUDED.health, integration_status.health),
                    setup_warnings = EXCLUDED.setup_warnings,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                {
                    "tenant_id": tenant_id,
                    "provider": provider,
                    "status": status_value,
                    "health": health,
                    "setup_warnings": _jsonb(list(setup_warnings or [])),
                    "metadata": _jsonb(dict(metadata or {})),
                    "updated_at": _utcnow(),
                },
            )
        if row is None:
            return None
        return {
            "tenantId": row.get("tenant_id"),
            "provider": row.get("provider"),
            "status": row.get("status"),
            "health": row.get("health"),
            "setupWarnings": list(row.get("setup_warnings") or []),
            "metadata": dict(row.get("metadata") or {}),
            "updatedAt": row.get("updated_at"),
        }


class SupabaseAuditLogRepository(_RepositoryBase, AuditLogRepository):
    """Postgres-backed repository for dashboard administrative audit logs."""

    async def create(self, log: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = dict(log)
        async with self._engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO audit_logs (
                        id,
                        tenant_id,
                        actor_user_id,
                        actor_email,
                        action,
                        resource_type,
                        resource_id,
                        before_payload,
                        after_payload,
                        timestamp
                    ) VALUES (
                        :id,
                        :tenant_id,
                        :actor_user_id,
                        :actor_email,
                        :action,
                        :resource_type,
                        :resource_id,
                        CAST(:before_payload AS jsonb),
                        CAST(:after_payload AS jsonb),
                        :timestamp
                    )
                    """
                ),
                {
                    "id": str(uuid4()),
                    "tenant_id": payload.get("tenantId"),
                    "actor_user_id": payload.get("actorUserId"),
                    "actor_email": payload.get("actorEmail"),
                    "action": payload.get("action"),
                    "resource_type": payload.get("resourceType"),
                    "resource_id": payload.get("resourceId"),
                    "before_payload": _jsonb(payload.get("before")),
                    "after_payload": _jsonb(payload.get("after")),
                    "timestamp": payload.get("timestamp") or _utcnow(),
                },
            )
        return payload


class SupabaseBillingSubscriptionRepository(_RepositoryBase, BillingSubscriptionRepository):
    """Postgres-backed repository for Stripe subscription state."""

    def _row_to_document(self, row: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "tenantId": row.get("tenant_id"),
            "stripeCustomerId": row.get("stripe_customer_id"),
            "stripeSubscriptionId": row.get("stripe_subscription_id"),
            "status": row.get("status"),
            "currentPeriodEnd": row.get("current_period_end"),
            "priceId": row.get("price_id"),
            "updatedAt": row.get("updated_at"),
        }

    async def get_by_tenant_id(self, tenant_id: str) -> Mapping[str, Any] | None:
        async with self._engine.connect() as connection:
            row = await _fetchone(
                connection,
                """
                SELECT *
                FROM billing_subscriptions
                WHERE tenant_id = :tenant_id
                LIMIT 1
                """,
                {"tenant_id": tenant_id},
            )
        return self._row_to_document(row)

    async def upsert_by_tenant_id(
        self,
        tenant_id: str,
        data: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        current = await self.get_by_tenant_id(tenant_id)
        merged = {**dict(current or {}), **dict(data), "tenantId": tenant_id, "updatedAt": _utcnow()}
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                INSERT INTO billing_subscriptions (
                    tenant_id,
                    stripe_customer_id,
                    stripe_subscription_id,
                    status,
                    current_period_end,
                    price_id,
                    updated_at
                ) VALUES (
                    :tenant_id,
                    :stripe_customer_id,
                    :stripe_subscription_id,
                    :status,
                    :current_period_end,
                    :price_id,
                    :updated_at
                )
                ON CONFLICT (tenant_id) DO UPDATE
                SET
                    stripe_customer_id = EXCLUDED.stripe_customer_id,
                    stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                    status = EXCLUDED.status,
                    current_period_end = EXCLUDED.current_period_end,
                    price_id = EXCLUDED.price_id,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                {
                    "tenant_id": tenant_id,
                    "stripe_customer_id": merged.get("stripeCustomerId"),
                    "stripe_subscription_id": merged.get("stripeSubscriptionId"),
                    "status": merged.get("status"),
                    "current_period_end": merged.get("currentPeriodEnd"),
                    "price_id": merged.get("priceId"),
                    "updated_at": merged.get("updatedAt"),
                },
            )
        return self._row_to_document(row)

    async def get_by_stripe_ids(
        self,
        *,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
    ) -> Mapping[str, Any] | None:
        if not stripe_customer_id and not stripe_subscription_id:
            return None

        clauses: list[str] = []
        params: dict[str, Any] = {}
        if stripe_customer_id:
            clauses.append("stripe_customer_id = :stripe_customer_id")
            params["stripe_customer_id"] = stripe_customer_id
        if stripe_subscription_id:
            clauses.append("stripe_subscription_id = :stripe_subscription_id")
            params["stripe_subscription_id"] = stripe_subscription_id

        async with self._engine.connect() as connection:
            row = await _fetchone(
                connection,
                f"""
                SELECT *
                FROM billing_subscriptions
                WHERE {' OR '.join(clauses)}
                LIMIT 1
                """,
                params,
            )
        return self._row_to_document(row)


class SupabaseProviderEventRepository(_RepositoryBase, ProviderEventRepository):
    """Postgres-backed repository for provider webhook idempotency."""

    async def record_once(
        self,
        *,
        provider: str,
        event_id: str,
        event_type: str,
        tenant_id: str | None,
        payload_hash: str,
    ) -> bool:
        async with self._engine.begin() as connection:
            row = await _fetchone(
                connection,
                """
                INSERT INTO provider_events (
                    provider,
                    event_id,
                    event_type,
                    tenant_id,
                    payload_hash,
                    created_at
                ) VALUES (
                    :provider,
                    :event_id,
                    :event_type,
                    :tenant_id,
                    :payload_hash,
                    :created_at
                )
                ON CONFLICT (provider, event_id) DO NOTHING
                RETURNING provider
                """,
                {
                    "provider": provider,
                    "event_id": event_id,
                    "event_type": event_type,
                    "tenant_id": tenant_id,
                    "payload_hash": payload_hash,
                    "created_at": _utcnow(),
                },
            )
        return row is not None


class SupabaseDatabase(Database):
    """Top-level Supabase/Postgres adapter that wires all repositories."""

    def __init__(
        self,
        settings: Settings | None = None,
        engine: AsyncEngine | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._engine = engine
        self._session_state_repo = SupabaseSessionStateRepository(self)
        self._knowledge_base_repo = SupabaseKnowledgeBaseRepository(self)
        self._governance_logs_repo = SupabaseGovernanceLogRepository(self)
        self._tenants_repo = SupabaseTenantRepository(self)
        self._audit_logs_repo = SupabaseAuditLogRepository(self)
        self._billing_subscriptions_repo = SupabaseBillingSubscriptionRepository(self)
        self._provider_events_repo = SupabaseProviderEventRepository(self)

    @property
    def session_state(self) -> SessionStateRepository:
        return self._session_state_repo

    @property
    def knowledge_base(self) -> KnowledgeBaseRepository:
        return self._knowledge_base_repo

    @property
    def governance_logs(self) -> GovernanceLogRepository:
        return self._governance_logs_repo

    @property
    def tenants(self) -> TenantRepository:
        return self._tenants_repo

    @property
    def audit_logs(self) -> AuditLogRepository:
        return self._audit_logs_repo

    @property
    def billing_subscriptions(self) -> BillingSubscriptionRepository:
        return self._billing_subscriptions_repo

    @property
    def provider_events(self) -> ProviderEventRepository:
        return self._provider_events_repo

    async def connect(self) -> None:
        if self._engine is None:
            database_url = self._settings.DATABASE_URL
            if database_url is None or not database_url.strip():
                raise DatabaseError("DATABASE_URL is not configured")
            self._engine = create_async_engine(
                _normalize_database_url(database_url),
                poolclass=NullPool,
                pool_pre_ping=True,
                connect_args={"prepare_threshold": None},
            )

        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def disconnect(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
