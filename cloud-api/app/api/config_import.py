from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.database import get_db
from ..services.camera_config_import import import_cameras_from_yaml


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
)


@router.post("/import-camera-config")
async def import_camera_config(
    db: AsyncSession = Depends(get_db),
):
    try:
        return await import_cameras_from_yaml(
            db,
            settings.camera_config_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
