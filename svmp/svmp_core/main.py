"""FastAPI application factory and runtime wiring for SVMP."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from svmp_core.config import Settings, get_dashboard_cors_origins, get_settings
from svmp_core.db.base import Database
from svmp_core.db.supabase import SupabaseDatabase
from svmp_core.logger import configure_logging
from svmp_core.routes import (
    build_billing_router,
    build_dashboard_router,
    build_internal_jobs_router,
    build_onboarding_router,
    build_webhook_router,
)


def create_app(
    *,
    settings: Settings | None = None,
    database: Database | None = None,
) -> FastAPI:
    """Create the SVMP FastAPI application with runtime dependencies wired."""

    runtime_settings = settings or get_settings()
    runtime_database = database or SupabaseDatabase(settings=runtime_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime_settings.validate_runtime()
        configure_logging()
        await runtime_database.connect()

        app.state.settings = runtime_settings
        app.state.database = runtime_database

        try:
            yield
        finally:
            await runtime_database.disconnect()

    app = FastAPI(title=runtime_settings.APP_NAME, lifespan=lifespan)

    dashboard_cors_origins = get_dashboard_cors_origins(runtime_settings)
    if dashboard_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=dashboard_cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-SVMP-Organization-Id",
                "X-SVMP-User-Email",
                "X-SVMP-User-Id",
            ],
        )

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        """Simple health endpoint for boot and smoke tests."""

        return {"status": "ok"}

    app.include_router(build_dashboard_router())
    app.include_router(build_billing_router())
    app.include_router(build_webhook_router(runtime_database, settings=runtime_settings))
    app.include_router(build_onboarding_router(runtime_database, settings=runtime_settings))
    app.include_router(build_internal_jobs_router())

    return app


app = create_app()
