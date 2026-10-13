from ..config import settings
from ..db.models import Alarm
from .notification import notify_alarm


async def create_alarm(db, event, redis_client):
    key = f"alarm:{event.camera_id}:{event.event_type}:{event.zone_id or 'none'}"

    if await redis_client.exists(key):
        return None

    alarm = Alarm(
        event_id=event.id,
        tenant_id=event.tenant_id,
        severity="HIGH",
        status="NEW",
    )
    db.add(alarm)
    await db.flush()
    await redis_client.set(key, "1", ex=settings.cooldown_seconds)
    await notify_alarm(alarm, event)
    return alarm
