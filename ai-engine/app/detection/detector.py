import logging
from pathlib import Path

from ultralytics import YOLO

from .types import Detection

logger = logging.getLogger(__name__)


class ObjectDetector:
    """YOLO26-compatible object detector with persistent per-camera tracking."""

    def __init__(
        self,
        model_path: str,
        confidence: float,
        image_size: int = 416,
        device: str = "cpu",
        tracker: str = "bytetrack.yaml",
        classes: list[int] | None = None,
        max_detections: int = 100,
    ):
        # Resolve relative model paths from the ai-engine directory, not the
        # caller's current working directory.
        engine_dir = Path(__file__).resolve().parents[2]
        requested_path = Path(model_path).expanduser()
        model_file = requested_path if requested_path.is_absolute() else engine_dir / requested_path
        model_path_for_ultralytics = str(model_file)

        if not model_file.exists() and not Path(model_path).is_absolute():
            # Let Ultralytics download official .pt weights when requested.
            if model_path.endswith(".pt"):
                model_path_for_ultralytics = model_path
            else:
                raise FileNotFoundError(
                    f"YOLO model not found: {model_file}. Run `python export.py` "
                    "from the ai-engine directory to create yolo26n_openvino_model, "
                    "or set MODEL_PATH to an existing model."
                )

        self.image_size = int(image_size)
        self.device = (device or "cpu").strip()
        self.tracker = tracker
        self.classes = classes if classes is not None else [0, 2]
        self.max_detections = int(max_detections)
        self.confidence = float(confidence)

        is_openvino = "_openvino_model" in model_path_for_ultralytics.lower()
        if is_openvino and self.device.lower() == "cpu":
            self.device = "intel:cpu"
        elif not is_openvino and self.device.lower() == "intel:cpu":
            self.device = "cpu"

        logger.info(
            "Loading YOLO model path=%s device=%s imgsz=%s tracker=%s classes=%s",
            model_path_for_ultralytics,
            self.device,
            self.image_size,
            self.tracker,
            self.classes,
        )
        self.model = YOLO(model_path_for_ultralytics)
        logger.info(
            "YOLO model loaded names=%s confidence=%.2f",
            getattr(self.model, "names", {}),
            self.confidence,
        )

    def detect(self, frame) -> list[Detection]:
        """Detect configured classes and attach persistent tracker IDs."""
        result = self.model.track(
            source=frame,
            persist=True,
            conf=self.confidence,
            classes=self.classes or None,
            tracker=self.tracker,
            imgsz=self.image_size,
            device=self.device,
            max_det=self.max_detections,
            verbose=False,
        )[0]

        if result.boxes is None or result.boxes.id is None:
            return []

        detections = []
        for box in result.boxes:
            if box.id is None:
                continue
            coordinates = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())
            names = self.model.names
            class_name = names.get(class_id, str(class_id)) if isinstance(names, dict) else names[class_id]
            detections.append(
                Detection(
                    track_id=int(box.id[0].item()),
                    class_id=class_id,
                    class_name=class_name,
                    confidence=float(box.conf[0].item()),
                    x1=float(coordinates[0]),
                    y1=float(coordinates[1]),
                    x2=float(coordinates[2]),
                    y2=float(coordinates[3]),
                )
            )
        return detections
