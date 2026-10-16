import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .api.alarms import router as alarms_router
from .api.cameras import router as cameras_router
from .api.config_import import router as config_import_router
from .api.events import router as events_router
from .config import settings
from .db import models  # noqa: F401
from .db.database import Base, engine
from .logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and storage before serving requests."""
    logger.info("Starting Cloud API; initializing database schema")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialization completed")
    except Exception:
        logger.exception("Database schema initialization failed")
        raise

    storage_path = Path(settings.storage_path)
    (storage_path / "snapshots").mkdir(
        parents=True,
        exist_ok=True,
    )
    logger.info("Snapshot storage ready at %s", storage_path)
    yield
    logger.info("Shutting down Cloud API")


app = FastAPI(
    title="CCTV AI Cloud API",
    version="0.2.2-debug",
    lifespan=lifespan,
)

app.include_router(cameras_router)
app.include_router(config_import_router)
app.include_router(events_router)
app.include_router(alarms_router)

Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
app.mount(
    "/media",
    StaticFiles(directory=settings.storage_path),
    name="media",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request method, path, status and duration without query secrets."""
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "Request failed method=%s path=%s duration_ms=%.1f",
            request.method, request.url.path, elapsed_ms,
        )
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    log_method = logger.warning if response.status_code >= 400 else logger.info
    log_method(
        "Request method=%s path=%s status=%s duration_ms=%.1f",
        request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


# Added after the request logger so CORS is the outermost user middleware and
# adds CORS headers to normal responses, preflight requests, and error responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "CCTV AI Cloud API",
        "version": "0.2.2-debug",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "cloud-api"}


@app.get("/health/db")
async def database_health():
    """Check actual database connectivity for troubleshooting."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable; inspect cloud-api logs",
        ) from exc
