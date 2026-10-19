from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cloud_api_url: str = "http://localhost:8000"
    cloud_api_key: str = "change-me"

    # For Intel CPU, export yolo26n.pt to yolo26n_openvino_model first.
    model_path: str = "yolo26n_openvino_model"
    confidence: float = 0.50
    image_size: int = 416
    device: str = "cpu"
    tracker: str = "bytetrack.yaml"
    # COCO class IDs: 0=person, 2=car. Use "0" for person-only detection.
    detection_classes: str = "0,2"
    max_detections: int = 100

    # Extra delay after each processed frame; 0 means yield without extra delay.
    ai_poll_interval: float = 0.0
    ai_camera_id: str = ""

    dw_enabled: bool = False
    dw_api_mode: str = "legacy"
    dw_url: str = "https://127.0.0.1:7001"
    dw_username: str = ""
    dw_password: str = ""
    dw_verify_ssl: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
