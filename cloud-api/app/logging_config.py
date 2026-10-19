import logging
import os


def configure_logging() -> None:
    """Configure consistent, container-friendly application logging."""
    default_level = (
        "DEBUG"
        if os.getenv("DEBUG_LOGGING", "false").lower() == "true"
        else "INFO"
    )
    level_name = os.getenv("LOG_LEVEL", default_level).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
    dependency_level = logging.INFO if level == logging.DEBUG else logging.WARNING
    logging.getLogger("httpx").setLevel(dependency_level)
    logging.getLogger("httpcore").setLevel(dependency_level)
