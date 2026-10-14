import json
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


class DWConnector:
    """Adapter for DW Spectrum Generic Event APIs."""

    def __init__(self, server_url, username, password, mode, verify_ssl):
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.mode = mode
        self.verify_ssl = verify_ssl

    async def send_event(self, camera_id, event_type, description):
        logger.debug("Posting DW Spectrum event mode=%s camera_id=%s type=%s", self.mode, camera_id, event_type)
        if self.mode == "rest_v4":
            return await self._send_rest_v4(camera_id, event_type, description)
        return await self._send_legacy(camera_id, event_type, description)

    async def _send_legacy(self, camera_id, event_type, description):
        params = {
            "source": json.dumps("AI"),
            "caption": json.dumps(event_type),
            "description": json.dumps(description),
            "metadata": json.dumps({"cameraRefs": [camera_id]}),
        }
        async with httpx.AsyncClient(
            verify=self.verify_ssl,
            auth=(self.username, self.password),
            timeout=10,
        ) as client:
            response = await client.get(
                f"{self.server_url}/api/createEvent", params=params
            )
            if response.is_error:
                logger.error("DW Spectrum legacy API failed status=%s response=%s", response.status_code, response.text[:500])
            response.raise_for_status()
            logger.debug("DW Spectrum legacy API accepted event status=%s", response.status_code)
            return response.text

    async def _send_rest_v4(self, camera_id, event_type, description):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": "instant",
            "source": "AI",
            "caption": event_type,
            "description": description,
            "deviceIds": [camera_id],
        }
        async with httpx.AsyncClient(
            verify=self.verify_ssl,
            auth=(self.username, self.password),
            timeout=10,
        ) as client:
            response = await client.post(
                f"{self.server_url}/rest/v4/events/generic", json=payload
            )
            if response.is_error:
                logger.error("DW Spectrum REST v4 API failed status=%s response=%s", response.status_code, response.text[:500])
            response.raise_for_status()
            logger.debug("DW Spectrum REST v4 API accepted event status=%s", response.status_code)
            return response.json()
