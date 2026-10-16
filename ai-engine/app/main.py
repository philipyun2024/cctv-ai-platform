import asyncio
import logging
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
from .logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


import logging
import json
import os

logger = logging.getLogger(__name__)


def debug_ai_engine_config(config, cameras=None):
    """Print AI Engine configuration and all loaded cameras."""
    logger.debug("========== AI ENGINE CONFIG ==========")

    if hasattr(config, "model_dump"):
        config_data = config.model_dump(mode="json")
    elif hasattr(config, "dict") and callable(config.dict):
        config_data = config.dict()
    elif isinstance(config, dict):
        config_data = config
    elif hasattr(config, "__dict__"):
        config_data = vars(config)
    else:
        config_data = str(config)

    logger.debug(
        "AI Engine config:\n%s",
        json.dumps(config_data, indent=2, default=str),
    )

    logger.debug("========== ENVIRONMENT SETTINGS ==========")
    logger.debug("AI_CONFIG_MODE=%s", os.getenv("AI_CONFIG_MODE"))
    logger.debug("CLOUD_API_URL=%s", os.getenv("CLOUD_API_URL"))

    if cameras is not None:
        logger.debug("========== ALL CAMERAS ==========")

        camera_data = []
        for camera in cameras:
            if hasattr(camera, "model_dump"):
                camera_data.append(camera.model_dump(mode="json"))
            elif hasattr(camera, "dict") and callable(camera.dict):
                camera_data.append(camera.dict())
            elif isinstance(camera, dict):
                camera_data.append(camera)
            elif hasattr(camera, "__dict__"):
                camera_data.append(vars(camera))
            else:
                camera_data.append(str(camera))

        logger.debug(
            "Camera count: %d\n%s",
            len(camera_data),
            json.dumps(camera_data, indent=2, default=str),
        )

    logger.debug("========== END DEBUG CONFIG ==========")

async def load_cameras() -> list[dict]:
    """Load camera definitions from YAML or Cloud API."""
    mode = os.getenv("AI_CONFIG_MODE", "cloud").lower()
    logger.info("Loading camera configuration mode=%s", mode)

    if mode == "yaml":
        path = os.getenv("AI_CONFIG_PATH", "../config/cameras.example.yaml")
        cameras = load_cameras_from_yaml(path)
        logger.info("Loaded %s cameras from YAML config path=%s", len(cameras), path)
        return cameras

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{settings.cloud_api_url}/api/v1/cameras")
        response.raise_for_status()
        cameras = response.json()
        logger.info("Cloud API returned %s cameras", len(cameras))

        debug_ai_engine_config(settings, cameras)

        if settings.ai_camera_id:
            cameras = [camera for camera in cameras if camera["dw_camera_id"] == settings.ai_camera_id]
            logger.info("Filtered cameras by AI_CAMERA_ID; remaining=%s", len(cameras))

        for camera in cameras:
            zone_response = await client.get(
                f"{settings.cloud_api_url}/api/v1/cameras/{camera['id']}/zones"
            )
            zone_response.raise_for_status()
            camera["zones"] = zone_response.json()
            logger.debug(
                "Loaded %s zones for camera=%s",
                len(camera["zones"]), camera.get("name", camera["id"]),
            )

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
    camera_name = camera.get("name", str(camera.get("id", "unknown")))
    logger.info("Starting camera worker camera=%s id=%s", camera_name, camera.get("id"))
    stream = CameraStream(camera["rtsp_url"], camera_name)
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
        try:
            first_frame = stream.read()
        except Exception:
            logger.exception("Waiting for camera stream camera=%s; retrying", camera_name)
        if first_frame is None:
            await asyncio.sleep(2)

    frame_height, frame_width = first_frame.shape[:2]
    rules = build_rules(camera, frame_width, frame_height)
    logger.info("Camera initialized camera=%s frame=%sx%s zones=%s", camera_name, frame_width, frame_height, len(rules))

    while True:
        try:
            frame = stream.read()
        except Exception:
            logger.exception("Stream read exception camera=%s", camera_name)
            await asyncio.sleep(2)
            continue
        if frame is None:
            await asyncio.sleep(0.5)
            continue

        detections = detector.detect(frame)
        logger.debug("Frame processed camera=%s detections=%s \ndetails:\n%s", camera_name, len(detections), json.dumps(detections, indent=2, default=str))
        for detection in detections:
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
                    logger.info("AI event submitted camera=%s type=%s event_id=%s alarm_id=%s", camera_name, event_type, result.get("event_id"), result.get("alarm_id"))

                    if (
                        settings.dw_enabled
                        and camera.get("dw_camera_id")
                    ):
                        logger.debug("Sending DW Spectrum event camera=%s type=%s", camera_name, event_type)
                        dw_result = await dw.send_event(
                            camera["dw_camera_id"],
                            event_type.title(),
                            f"AI {event_type} detected.",
                        )
                        logger.info("DW Spectrum event sent camera=%s result_type=%s", camera_name, type(dw_result).__name__)
                except Exception:
                    logger.exception("Unable to submit AI event camera=%s type=%s", camera_name, event_type)

        await asyncio.sleep(settings.ai_poll_interval)


async def main() -> None:
    logger.info("AI engine starting model=%s confidence=%.2f poll_interval=%.2f", settings.model_path, settings.confidence, settings.ai_poll_interval)
    cameras = [
        camera for camera in await load_cameras()
        if camera.get("enabled", True)
    ]

    if not cameras:
        logger.error("No enabled cameras found. Check Cloud API database or camera YAML configuration.")
        return

    logger.info("Launching workers for %s enabled cameras", len(cameras))
    await asyncio.gather(*(process_camera(camera) for camera in cameras))


if __name__ == "__main__":
    asyncio.run(main())
