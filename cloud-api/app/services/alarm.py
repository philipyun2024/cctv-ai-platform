import logging

from ..config import settings
from ..db.models import Alarm
from .notification import notify_alarm

logger = logging.getLogger(__name__)


async def create_alarm(db, event, redis_client):
    key = f"alarm:{event.camera_id}:{event.event_type}:{event.zone_id or 'none'}"

    if await redis_client.exists(key):
        logger.info("Alarm suppressed by cooldown camera_id=%s event_type=%s zone_id=%s", event.camera_id, event.event_type, event.zone_id)
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
    logger.info("Alarm created alarm_id=%s event_id=%s severity=%s", alarm.id, event.id, alarm.severity)
    await notify_alarm(alarm, event)
    return alarm
