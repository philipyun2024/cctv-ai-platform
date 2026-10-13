from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..db.models import Alarm, Event

router = APIRouter(prefix="/api/v1/alarms", tags=["alarms"])


@router.get("")
async def list_alarms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alarm).order_by(Alarm.triggered_at.desc()).limit(100))
    return [
        {
            "id": str(alarm.id),
            "event_id": str(alarm.event_id),
            "severity": alarm.severity,
            "status": alarm.status,
            "triggered_at": alarm.triggered_at,
        }
        for alarm in result.scalars()
    ]


async def update_status(alarm_id: UUID, status: str, db: AsyncSession):
    alarm = await db.get(Alarm, alarm_id)
    if alarm is None:
        raise HTTPException(status_code=404, detail="Alarm not found")
    alarm.status = status
    now = datetime.now(timezone.utc)
    if status == "ACKNOWLEDGED":
        alarm.acknowledged_at = now
    if status == "RESOLVED":
        alarm.resolved_at = now
    await db.commit()
    return {"status": status.lower()}


@router.post("/{alarm_id}/acknowledge")
async def acknowledge(alarm_id: UUID, db: AsyncSession = Depends(get_db)):
    return await update_status(alarm_id, "ACKNOWLEDGED", db)


@router.post("/{alarm_id}/resolve")
async def resolve(alarm_id: UUID, db: AsyncSession = Depends(get_db)):
    return await update_status(alarm_id, "RESOLVED", db)


@router.get("/{alarm_id}")
async def detail(alarm_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alarm, Event).join(Event, Event.id == Alarm.event_id).where(Alarm.id == alarm_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Alarm not found")
    alarm, event = row
    return {
        "alarm": {"id": str(alarm.id), "severity": alarm.severity, "status": alarm.status},
        "event": {
            "id": str(event.id),
            "camera_id": str(event.camera_id),
            "event_type": event.event_type,
            "confidence": event.confidence,
            "timestamp": event.timestamp,
            "snapshot_url": event.snapshot_url,
            "metadata": event.metadata,
        },
    }
