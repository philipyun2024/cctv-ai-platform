from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Camera, Zone


def load_camera_config(path: str) -> dict:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Camera configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file_handle:
        return yaml.safe_load(file_handle) or {}


async def import_cameras_from_yaml(
    db: AsyncSession,
    path: str,
) -> dict:
    """Idempotently import camera and zone definitions from YAML."""
    document = load_camera_config(path)
    cameras_added = 0
    cameras_updated = 0
    zones_added = 0
    zones_updated = 0

    for item in document.get("cameras", []):
        site_id = item.get("site_id", "demo-site")
        result = await db.execute(
            select(Camera).where(
                Camera.site_id == site_id,
                Camera.name == item["name"],
            )
        )
        camera = result.scalar_one_or_none()

        if camera is None:
            camera = Camera(
                site_id=site_id,
                name=item["name"],
                rtsp_url=item["rtsp_url"],
                dw_camera_id=item.get("dw_camera_id"),
                enabled=item.get("enabled", True),
            )
            db.add(camera)
            await db.flush()
            cameras_added += 1
        else:
            camera.rtsp_url = item["rtsp_url"]
            camera.dw_camera_id = item.get("dw_camera_id")
            camera.enabled = item.get("enabled", True)
            cameras_updated += 1

        for zone_item in item.get("zones", []):
            result = await db.execute(
                select(Zone).where(
                    Zone.camera_id == camera.id,
                    Zone.name == zone_item["name"],
                )
            )
            zone = result.scalar_one_or_none()

            zone_type = zone_item.get(
                "zone_type",
                zone_item.get("type", "intrusion"),
            )
            if zone is None:
                zone = Zone(
                    camera_id=camera.id,
                    name=zone_item["name"],
                    zone_type=zone_type,
                    points=zone_item["points"],
                    loitering_seconds=zone_item.get(
                        "loitering_seconds",
                        120,
                    ),
                    enabled=zone_item.get("enabled", True),
                )
                db.add(zone)
                zones_added += 1
            else:
                zone.zone_type = zone_type
                zone.points = zone_item["points"]
                zone.loitering_seconds = zone_item.get(
                    "loitering_seconds",
                    120,
                )
                zone.enabled = zone_item.get("enabled", True)
                zones_updated += 1

    await db.commit()
    return {
        "cameras_added": cameras_added,
        "cameras_updated": cameras_updated,
        "zones_added": zones_added,
        "zones_updated": zones_updated,
    }
