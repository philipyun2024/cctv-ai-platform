import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..db.models import Camera, Zone
from ..schemas import CameraCreate, ZoneCreate

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])
logger = logging.getLogger(__name__)


def serialize_camera(camera):
    return {
        "id": str(camera.id),
        "site_id": camera.site_id,
        "name": camera.name,
        "rtsp_url": camera.rtsp_url,
        "dw_camera_id": camera.dw_camera_id,
        "enabled": camera.enabled,
    }


def serialize_zone(zone):
    return {
        "id": str(zone.id),
        "camera_id": str(zone.camera_id),
        "name": zone.name,
        "zone_type": zone.zone_type,
        "points": zone.points,
        "loitering_seconds": zone.loitering_seconds,
        "enabled": zone.enabled,
    }


@router.post("")
async def create_camera(payload: CameraCreate, db: AsyncSession = Depends(get_db)):
    logger.info("Creating camera name=%s site_id=%s", payload.name, payload.site_id)
    camera = Camera(**payload.model_dump())
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return serialize_camera(camera)


@router.get("")
async def list_cameras(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Camera).order_by(Camera.created_at.desc()))
    cameras = [serialize_camera(camera) for camera in result.scalars()]
    logger.debug("Listed cameras count=%s", len(cameras))
    return cameras


@router.post("/{camera_id}/zones")
async def create_zone(
    camera_id: UUID,
    payload: ZoneCreate,
    db: AsyncSession = Depends(get_db),
):
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    logger.info("Creating zone camera_id=%s name=%s type=%s", camera_id, payload.name, payload.zone_type)
    zone = Zone(camera_id=camera_id, **payload.model_dump())
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return serialize_zone(zone)


@router.get("/{camera_id}/zones")
async def list_zones(camera_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Zone).where(Zone.camera_id == camera_id))
    return [serialize_zone(zone) for zone in result.scalars()]
