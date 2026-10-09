import asyncio

import httpx

from .camera.stream import CameraStream
from .cloud.client import CloudClient
from .config import settings
from .detection.detector import ObjectDetector
from .dw.connector import DWConnector
from .rules.intrusion import IntrusionDetector
from .rules.loitering import LoiteringDetector
from .rules.zone import Zone


async def get_json(path):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{settings.cloud_api_url}{path}")
        response.raise_for_status()
        return response.json()


async def process_camera(camera):
    stream = CameraStream(camera["rtsp_url"])
    detector = ObjectDetector(settings.model_path, settings.confidence)
    cloud = CloudClient(settings.cloud_api_url, settings.cloud_api_key)
    dw = DWConnector(
        settings.dw_url,
        settings.dw_username,
        settings.dw_password,
        settings.dw_api_mode,
        settings.dw_verify_ssl,
    )

    zones_config = await get_json(f"/api/v1/cameras/{camera['id']}/zones")
    first_frame = None
    while first_frame is None:
        first_frame = stream.read()
        await asyncio.sleep(0.1)

    height, width = first_frame.shape[:2]
    rules = []
    for config in zones_config:
        if not config["enabled"]:
            continue
        zone = Zone(config["id"], config["name"], config["points"], width, height)
        intrusion = IntrusionDetector(zone) if config["zone_type"] == "intrusion" else None
        loitering = (
            LoiteringDetector(zone, config["loitering_seconds"])
            if config["zone_type"] == "loitering"
            else None
        )
        rules.append((config, intrusion, loitering))

    while True:
        frame = stream.read()
        if frame is None:
            await asyncio.sleep(0.5)
            continue
        for detection in detector.detect(frame):
            for config, intrusion, loitering in rules:
                event_type = None
                if intrusion and intrusion.check(detection):
                    event_type = "intrusion"
                if loitering and loitering.check(detection):
                    event_type = "loitering"
                if event_type is None:
                    continue
                try:
                    result = await cloud.send_event(
                        "demo-tenant",
                        camera["site_id"],
                        camera["id"],
                        event_type,
                        detection.confidence,
                        detection.track_id,
                        config["id"],
                        frame,
                        {"class_name": detection.class_name},
                    )
                    print("AI event sent:", result)
                    if settings.dw_enabled and camera.get("dw_camera_id"):
                        await dw.send_event(
                            camera["dw_camera_id"],
                            event_type.title(),
                            f"AI {event_type} detected.",
                        )
                except Exception as exc:
                    print("Unable to send event:", exc)
        await asyncio.sleep(settings.ai_poll_interval)


async def main():
    cameras = await get_json("/api/v1/cameras")
    if settings.ai_camera_id:
        cameras = [c for c in cameras if c["id"] == settings.ai_camera_id]
    cameras = [c for c in cameras if c["enabled"]]
    if not cameras:
        print("No enabled cameras found.")
        return
    await asyncio.gather(*(process_camera(camera) for camera in cameras))


if __name__ == "__main__":
    asyncio.run(main())
