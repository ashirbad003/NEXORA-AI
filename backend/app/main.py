from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.schemas.auth import HealthResponse
from backend.app.api import (
    auth, students, admin, placement, learning, coding, copilot, assessments,
    interview, resume, github, jobs, placement_cell, admin_intelligence,
    revision, peer, notifications, sync
)
from backend.app.services.scheduler_service import scheduler
from backend.app.services.websocket_manager import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Notification Background Scheduler & WebSocket Event Bus Listener
    await scheduler.start()
    await ws_manager.start_listener()
    yield
    # Shutdown: Stop Scheduler & Event Bus cleanly
    await scheduler.stop()
    await ws_manager.stop_listener()

def create_app() -> FastAPI:
    setup_logging(debug=settings.APP_DEBUG)
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Unified Career, Learning, Coding & Placement Platform API",
        version="1.0.0",
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID, Telemetry & Security Headers Middleware
    @app.middleware("http")
    async def security_and_telemetry_middleware(request: Request, call_next):
        # 1. Payload size guard: Max 10MB to prevent memory exhaustion DoS
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload too large. Maximum permitted request body is 10MB.", "type": "PAYLOAD_TOO_LARGE"}
            )

        # 2. Correlation ID: validate and enforce length limit (max 64 chars, alphanumeric/dashes)
        raw_req_id = request.headers.get("X-Request-ID")
        if raw_req_id and len(raw_req_id) <= 64 and raw_req_id.replace("-", "").replace("_", "").isalnum():
            request_id = raw_req_id
        else:
            request_id = str(uuid.uuid4())

        from backend.app.core.telemetry import request_id_ctx, metrics
        token_ctx = request_id_ctx.set(request_id)
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Reference ID logged.", "type": "INTERNAL_ERROR"}
            )
        finally:
            process_time_ms = round((time.time() - start_time) * 1000, 2)
            request_id_ctx.reset(token_ctx)

        # 3. Observability telemetry recording
        metrics.record_request(request.method, request.url.path, response.status_code, process_time_ms)

        # 4. Invariant HTTP Security Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = str(process_time_ms)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Sensitive route cache prevention
        if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/sync"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        logger.info(
            f"{request.method} {request.url.path} - Status: {response.status_code} ({process_time_ms}ms)"
        )
        return response

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Reference ID logged.", "type": "INTERNAL_ERROR"}
        )

    # Mount API v1 Routers
    app.include_router(auth.router, prefix=settings.API_V1_STR)
    app.include_router(students.router, prefix=settings.API_V1_STR)
    app.include_router(admin.router, prefix=settings.API_V1_STR)
    app.include_router(placement.router, prefix=settings.API_V1_STR)
    app.include_router(learning.router, prefix=settings.API_V1_STR)
    app.include_router(coding.router, prefix=settings.API_V1_STR)
    app.include_router(copilot.router, prefix=settings.API_V1_STR)
    app.include_router(assessments.router, prefix=settings.API_V1_STR)
    app.include_router(interview.router, prefix=settings.API_V1_STR)
    app.include_router(resume.router, prefix=settings.API_V1_STR)
    app.include_router(github.router, prefix=settings.API_V1_STR)
    app.include_router(jobs.router, prefix=settings.API_V1_STR)
    app.include_router(placement_cell.router, prefix=settings.API_V1_STR)
    app.include_router(admin_intelligence.router, prefix=settings.API_V1_STR)
    app.include_router(revision.router, prefix=settings.API_V1_STR)
    app.include_router(peer.router, prefix=settings.API_V1_STR)
    app.include_router(notifications.router, prefix=settings.API_V1_STR)
    app.include_router(sync.router, prefix=settings.API_V1_STR)

    # Health Check Endpoints
    @app.get("/health/live", tags=["System"])
    async def health_live():
        return {"status": "ok", "app": settings.APP_NAME}

    @app.get("/health/ready", response_model=HealthResponse, tags=["System"])
    async def health_ready():
        # Live DB connection probe
        db_status = "connected"
        try:
            from backend.app.db.session import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            db_status = "connected_sqlite_async" if "sqlite" in settings.DATABASE_URL else "connected_postgres"
        except Exception as e:
            logger.warning(f"Database readiness probe failed: {e}")
            db_status = "disconnected"

        return HealthResponse(
            status="healthy" if db_status != "disconnected" else "degraded",
            app=settings.APP_NAME,
            environment=settings.APP_ENV,
            database=db_status,
            ai_engine=f"provider_{settings.AI_PROVIDER}_ready",
            sandbox=f"mode_{settings.SANDBOX_MODE}_ready"
        )

    # Operational Telemetry Endpoint (Safe aggregate metrics)
    @app.get("/metrics", tags=["System"])
    async def get_metrics():
        from backend.app.core.telemetry import metrics
        return metrics.get_summary()

    @app.get("/", tags=["System"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "tagline": "Intelligence That Moves You Forward.",
            "docs": "/docs" if settings.APP_DEBUG else "disabled"
        }

    return app

app = create_app()
