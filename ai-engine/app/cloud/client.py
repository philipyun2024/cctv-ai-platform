import base64
import logging
from datetime import datetime, timezone

import cv2
import httpx

logger = logging.getLogger(__name__)


class CloudClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @staticmethod
    def encode_frame(frame):
        success, encoded = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
        )
        if not success:
            raise RuntimeError("Unable to encode event snapshot")
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    async def send_event(
        self,
        tenant_id,
        site_id,
        camera_id,
        event_type,
        confidence,
        track_id,
        zone_id,
        frame,
        metadata,
    ):
        payload = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "camera_id": camera_id,
            "event_type": event_type,
            "confidence": confidence,
            "track_id": track_id,
            "zone_id": zone_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "snapshot_base64": self.encode_frame(frame),
            "metadata": metadata,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/events",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if response.is_error:
                logger.error("Cloud API rejected event status=%s response=%s", response.status_code, response.text[:500])
            response.raise_for_status()
            logger.debug("Cloud API accepted event status=%s", response.status_code)
            return response.json()
