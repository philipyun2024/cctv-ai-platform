from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cloud_api_url: str = "http://localhost:8000"
    cloud_api_key: str = "change-me"
    model_path: str = "yolo11n.pt"
    confidence: float = 0.50
    ai_poll_interval: float = 0.25
    ai_camera_id: str = ""
    dw_enabled: bool = False
    dw_api_mode: str = "legacy"
    dw_url: str = "https://127.0.0.1:7001"
    dw_username: str = ""
    dw_password: str = ""
    dw_verify_ssl: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
