"""Internal stateless job routes for Vercel/Supabase cron execution."""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request, status

from svmp_core.config import Settings
from svmp_core.db.base import Database
from svmp_core.workflows import run_workflow_b, run_workflow_c


def _database_from_request(request: Request) -> Database:
    return request.app.state.database


def _settings_from_request(request: Request) -> Settings:
    return request.app.state.settings


def _secret_value(secret) -> str | None:
    if secret is None:
        return None
    value = secret.get_secret_value().strip()
    return value or None


def _bearer_token(authorization: str | None) -> str | None:
    if authorization is None or not authorization.strip():
        return None
    scheme, _, token = authorization.strip().partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _require_internal_job_auth(
    request: Request,
    authorization: str | None,
    job_secret_header: str | None,
) -> None:
    settings = _settings_from_request(request)
    expected_secret = _secret_value(settings.INTERNAL_JOB_SECRET)
    if expected_secret is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="internal job secret is not configured",
        )

    provided_secret = _bearer_token(authorization) or job_secret_header
    if provided_secret is None or not hmac.compare_digest(provided_secret, expected_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid internal job credentials",
        )


async def _run_workflow_b_batch(
    *,
    database: Database,
    settings: Settings,
    max_runs: int,
) -> dict[str, Any]:
    processed: list[dict[str, Any]] = []
    for _ in range(max(1, min(max_runs, settings.WORKFLOW_B_MAX_BATCH_SIZE))):
        result = await run_workflow_b(database, settings=settings)
        if not result.processed:
            break
        processed.append(
            {
                "sessionId": result.session_id,
                "decision": result.decision.value if result.decision is not None else None,
                "domainId": result.domain_id,
                "matcherUsed": result.matcher_used,
                "reason": result.reason,
            }
        )

    return {
        "status": "ok",
        "processedCount": len(processed),
        "drained": len(processed) < max_runs,
        "runs": processed,
    }


def build_internal_jobs_router() -> APIRouter:
    """Build authenticated internal job routes for stateless execution."""

    router = APIRouter(prefix="/internal", tags=["internal"])

    @router.post("/jobs/process-ready-sessions")
    async def process_ready_sessions(
        request: Request,
        max_runs: int = Query(default=25, alias="maxRuns", ge=1, le=100),
        authorization: str | None = Header(default=None, alias="Authorization"),
        job_secret_header: str | None = Header(default=None, alias="X-SVMP-Job-Secret"),
    ) -> dict[str, Any]:
        _require_internal_job_auth(request, authorization, job_secret_header)
        return await _run_workflow_b_batch(
            database=_database_from_request(request),
            settings=_settings_from_request(request),
            max_runs=max_runs,
        )

    @router.post("/jobs/cleanup-stale-sessions")
    async def cleanup_stale_sessions(
        request: Request,
        authorization: str | None = Header(default=None, alias="Authorization"),
        job_secret_header: str | None = Header(default=None, alias="X-SVMP-Job-Secret"),
    ) -> dict[str, Any]:
        _require_internal_job_auth(request, authorization, job_secret_header)
        result = await run_workflow_c(
            _database_from_request(request),
            settings=_settings_from_request(request),
        )
        return {
            "status": "ok",
            "staleSessionsFound": result.stale_sessions_found,
            "governanceLogsWritten": result.governance_logs_written,
            "sessionsDeleted": result.sessions_deleted,
            "cutoffTime": result.cutoff_time,
        }

    return router
