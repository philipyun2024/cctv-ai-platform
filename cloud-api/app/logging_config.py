import logging


def configure_logging(
    log_level: str | None = None,
    debug_logging: bool = False,
) -> None:
    """Configure logging using settings loaded from .env or process environment."""
    level_name = (log_level or ("DEBUG" if debug_logging else "INFO")).upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        level = logging.INFO
        level_name = "INFO"

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
    dependency_level = logging.INFO if level == logging.DEBUG else logging.WARNING
    logging.getLogger("httpx").setLevel(dependency_level)
    logging.getLogger("httpcore").setLevel(dependency_level)
