from pathlib import Path

import yaml


def load_cameras_from_yaml(path: str) -> list[dict]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Camera YAML file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file_handle:
        document = yaml.safe_load(file_handle) or {}

    return document.get("cameras", [])
