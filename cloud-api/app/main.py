from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.alarms import router as alarms_router
from .api.cameras import router as cameras_router
from .api.events import router as events_router
from .config import settings
from .db.database import Base, engine
from .db import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="CCTV AI Cloud API", version="0.2.0", lifespan=lifespan)
app.include_router(cameras_router)
app.include_router(events_router)
app.include_router(alarms_router)
app.mount("/media", StaticFiles(directory=settings.storage_path), name="media")


@app.get("/")
async def root():
    return {"name": "CCTV AI Cloud API", "version": "0.2.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
