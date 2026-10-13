import asyncio
import os

import httpx

from .camera.config_loader import load_cameras_from_yaml
from .camera.stream import CameraStream
from .cloud.client import CloudClient
from .config import settings
from .detection.detector import ObjectDetector
from .dw.connector import DWConnector
from .rules.intrusion import IntrusionDetector
from .rules.loitering import LoiteringDetector
from .rules.zone import Zone


async def load_cameras() -> list[dict]:
    """Load camera definitions from YAML or Cloud API."""
    mode = os.getenv("AI_CONFIG_MODE", "cloud").lower()

    if mode == "yaml":
        path = os.getenv(
            "AI_CONFIG_PATH",
            "../config/cameras.example.yaml",
        )
        return load_cameras_from_yaml(path)

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{settings.cloud_api_url}/api/v1/cameras",
        )
        response.raise_for_status()
        cameras = response.json()

        if settings.ai_camera_id:
            cameras = [
                camera for camera in cameras
                if camera["id"] == settings.ai_camera_id
            ]

        for camera in cameras:
            zone_response = await client.get(
                f"{settings.cloud_api_url}"
                f"/api/v1/cameras/{camera['id']}/zones",
            )
            zone_response.raise_for_status()
            camera["zones"] = zone_response.json()

        return cameras


def build_rules(
    camera: dict,
    frame_width: int,
    frame_height: int,
) -> list[dict]:
    rules = []

    for item in camera.get("zones", []):
        if not item.get("enabled", True):
            continue

        zone = Zone(
            str(item["id"]),
            item["name"],
            item["points"],
            frame_width,
            frame_height,
        )
        zone_type = item.get(
            "zone_type",
            item.get("type", "intrusion"),
        )

        rules.append({
            "config": item,
            "intrusion": (
                IntrusionDetector(zone)
                if zone_type == "intrusion"
                else None
            ),
            "loitering": (
                LoiteringDetector(
                    zone,
                    int(item.get("loitering_seconds", 120)),
                )
                if zone_type == "loitering"
                else None
            ),
        })

    return rules


async def process_camera(camera: dict) -> None:
    stream = CameraStream(camera["rtsp_url"])
    detector = ObjectDetector(
        settings.model_path,
        settings.confidence,
    )
    cloud = CloudClient(
        settings.cloud_api_url,
        settings.cloud_api_key,
    )
    dw = DWConnector(
        settings.dw_url,
        settings.dw_username,
        settings.dw_password,
        settings.dw_api_mode,
        settings.dw_verify_ssl,
    )

    first_frame = None
    while first_frame is None:
        first_frame = stream.read()
        await asyncio.sleep(0.1)

    frame_height, frame_width = first_frame.shape[:2]
    rules = build_rules(
        camera,
        frame_width,
        frame_height,
    )

    while True:
        frame = stream.read()
        if frame is None:
            await asyncio.sleep(0.5)
            continue

        for detection in detector.detect(frame):
            for rule in rules:
                event_type = None
                config = rule["config"]

                if (
                    rule["intrusion"]
                    and rule["intrusion"].check(detection)
                ):
                    event_type = "intrusion"

                if rule["loitering"]:
                    loitering_event = rule["loitering"].check(
                        detection
                    )
                    if loitering_event:
                        event_type = "loitering"

                if not event_type:
                    continue

                try:
                    result = await cloud.send_event(
                        tenant_id=camera.get(
                            "tenant_id",
                            "demo-tenant",
                        ),
                        site_id=camera.get(
                            "site_id",
                            "demo-site",
                        ),
                        camera_id=camera["id"],
                        event_type=event_type,
                        confidence=detection.confidence,
                        track_id=detection.track_id,
                        zone_id=str(config["id"]),
                        frame=frame,
                        metadata={
                            "class_name": detection.class_name,
                        },
                    )
                    print("AI event sent:", result)

                    if (
                        settings.dw_enabled
                        and camera.get("dw_camera_id")
                    ):
                        await dw.send_event(
                            camera["dw_camera_id"],
                            event_type.title(),
                            f"AI {event_type} detected.",
                        )
                except Exception as exc:
                    print("Unable to send event:", exc)

        await asyncio.sleep(settings.ai_poll_interval)


async def main() -> None:
    cameras = [
        camera for camera in await load_cameras()
        if camera.get("enabled", True)
    ]

    if not cameras:
        print("No enabled cameras found.")
        return

    await asyncio.gather(
        *(process_camera(camera) for camera in cameras)
    )


if __name__ == "__main__":
    asyncio.run(main())
