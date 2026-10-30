from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Logging settings are loaded from the service .env or process environment.
    log_level: str | None = None
    debug_logging: bool = False
    database_url: str = (
        "postgresql+asyncpg://cctv:cctv_password@localhost:5432/cctv"
    )
    redis_url: str = "redis://localhost:6379/0"
    storage_path: str = "./storage"
    snapshot_retention_days: int = 30
    snapshot_max_bytes: int = 8 * 1024 * 1024
    public_base_url: str = "http://localhost:8000"
    cooldown_seconds: int = 300
    camera_config_path: str = "/app/app/config/cameras.example.yaml"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
