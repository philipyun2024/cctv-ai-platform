import json

import httpx


class DWConnector:
    """Adapter for DW Spectrum Generic Event APIs."""

    def __init__(self, server_url, username, password, mode, verify_ssl):
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.mode = mode
        self.verify_ssl = verify_ssl

    async def send_event(self, camera_id, event_type, description):
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
            response.raise_for_status()
            return response.text

    async def _send_rest_v4(self, camera_id, event_type, description):
        payload = {
            "timestamp": None,
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
            response.raise_for_status()
            return response.json()
