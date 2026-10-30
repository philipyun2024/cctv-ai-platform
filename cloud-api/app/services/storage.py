import base64
import binascii
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)


def _decode_image(image_base64: str) -> bytes:
    """Decode a base64-encoded image and reject empty or oversized payloads."""
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    try:
        data = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Snapshot is not valid base64 data") from exc
    if not data:
        raise ValueError("Snapshot image is empty")
    if len(data) > settings.snapshot_max_bytes:
        raise ValueError(
            f"Snapshot exceeds maximum size of {settings.snapshot_max_bytes} bytes"
        )
    # JPEG and PNG signatures only; snapshots are normally JPEG.
    if not (data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG\r\n\x1a\n")):
        raise ValueError("Snapshot must be a JPEG or PNG image")
    return data


def save_snapshot(image_base64: str | None, image_kind: str = "original") -> str | None:
    """Persist one event image and return its public media URL."""
    if not image_base64:
        return None
    if image_kind not in {"original", "annotated"}:
        raise ValueError("Unsupported snapshot image kind")
    data = _decode_image(image_base64)
    folder = Path(settings.storage_path) / "snapshots"
    folder.mkdir(parents=True, exist_ok=True)
    extension = ".png" if data.startswith(b"\x89PNG") else ".jpg"
    filename = f"{uuid.uuid4()}_{image_kind}{extension}"
    destination = folder / filename
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)
    return (
        f"{settings.public_base_url.rstrip('/')}/media/snapshots/{filename}"
    )


def cleanup_expired_snapshots(retention_days: int | None = None) -> int:
    """Delete snapshot files older than the configured retention period."""
    days = retention_days or settings.snapshot_retention_days
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    folder = Path(settings.storage_path) / "snapshots"
    if not folder.exists():
        return 0
    deleted = 0
    for path in folder.iterdir():
        if not path.is_file() or path.name.endswith(".tmp"):
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1
        except OSError:
            logger.exception("Unable to remove expired snapshot path=%s", path)
    if deleted:
        logger.info("Expired snapshots removed count=%s retention_days=%s", deleted, days)
    return deleted
