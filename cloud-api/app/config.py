from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://cctv:cctv_password@localhost:5432/cctv"
    )
    redis_url: str = "redis://localhost:6379/0"
    storage_path: str = "./storage"
    public_base_url: str = "http://localhost:8000"
    cooldown_seconds: int = 300
    camera_config_path: str = "/app/app/config/cameras.example.yaml"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
