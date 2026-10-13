from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..db.models import Event
from ..main_dependencies import get_redis
from ..schemas import EventCreate
from ..services.alarm import create_alarm
from ..services.storage import save_snapshot

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("")
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    event = Event(
        tenant_id=payload.tenant_id,
        site_id=payload.site_id,
        camera_id=UUID(payload.camera_id),
        zone_id=UUID(payload.zone_id) if payload.zone_id else None,
        event_type=payload.event_type,
        confidence=payload.confidence,
        timestamp=payload.timestamp,
        track_id=payload.track_id,
        snapshot_url=save_snapshot(payload.snapshot_base64),
        metadata=payload.metadata,
    )
    db.add(event)
    await db.flush()

    alarm = None
    if payload.event_type in {"intrusion", "loitering"}:
        alarm = await create_alarm(db, event, redis_client)

    await db.commit()
    return {
        "event_id": str(event.id),
        "alarm_id": str(alarm.id) if alarm else None,
        "snapshot_url": event.snapshot_url,
    }
