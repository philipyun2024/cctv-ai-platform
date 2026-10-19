import base64
import uuid
from pathlib import Path

from ..config import settings


def save_snapshot(snapshot_base64: str | None) -> str | None:
    if not snapshot_base64:
        return None

    if "," in snapshot_base64:
        snapshot_base64 = snapshot_base64.split(",", 1)[1]

    data = base64.b64decode(snapshot_base64)
    folder = Path(settings.storage_path) / "snapshots"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.jpg"
    (folder / filename).write_bytes(data)
    return f"{settings.public_base_url.rstrip('/')}/media/snapshots/{filename}"
