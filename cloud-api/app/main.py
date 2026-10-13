from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.alarms import router as alarms_router
from .api.cameras import router as cameras_router
from .api.config_import import router as config_import_router
from .api.events import router as events_router
from .config import settings
from .db import models  # noqa: F401
from .db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and storage before serving requests."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    storage_path = Path(settings.storage_path)
    (storage_path / "snapshots").mkdir(
        parents=True,
        exist_ok=True,
    )
    yield


app = FastAPI(
    title="CCTV AI Cloud API",
    version="0.2.1",
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


@app.get("/")
async def root():
    return {
        "name": "CCTV AI Cloud API",
        "version": "0.2.1",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
