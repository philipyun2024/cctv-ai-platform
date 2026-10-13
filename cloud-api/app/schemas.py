from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CameraCreate(BaseModel):
    site_id: str
    name: str
    rtsp_url: str
    dw_camera_id: str | None = None
    enabled: bool = True


class ZoneCreate(BaseModel):
    name: str
    zone_type: str = Field(pattern="^(intrusion|loitering)$")
    points: list[list[float]]
    loitering_seconds: int = 120
    enabled: bool = True


class EventCreate(BaseModel):
    tenant_id: str
    site_id: str
    camera_id: str
    event_type: str
    confidence: float
    timestamp: datetime
    track_id: int | None = None
    zone_id: str | None = None
    snapshot_base64: str | None = None
    metadata: dict[str, Any] = {}
