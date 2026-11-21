from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.schemas.auth import HealthResponse
from backend.app.api import auth, students, admin, placement, learning, coding, copilot

def create_app() -> FastAPI:
    setup_logging(debug=settings.APP_DEBUG)
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Unified Career, Learning, Coding & Placement Platform API",
        version="1.0.0",
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and Latency Tracing Middleware
    @app.middleware("http")
    async def trace_and_log_requests(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = str(process_time_ms)
        
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

    # Health Check Endpoints
    @app.get("/health/live", tags=["System"])
    async def health_live():
        return {"status": "ok", "app": settings.APP_NAME}

    @app.get("/health/ready", response_model=HealthResponse, tags=["System"])
    async def health_ready():
        return HealthResponse(
            status="healthy",
            app=settings.APP_NAME,
            environment=settings.APP_ENV,
            database="connected_sqlite_async" if "sqlite" in settings.DATABASE_URL else "configured_postgres",
            ai_engine=f"provider_{settings.AI_PROVIDER}_ready",
            sandbox=f"mode_{settings.SANDBOX_MODE}_ready"
        )

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
