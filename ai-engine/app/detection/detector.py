import logging

from ultralytics import YOLO

from .types import Detection

logger = logging.getLogger(__name__)


class ObjectDetector:
    """YOLO detector with persistent tracking."""

    def __init__(self, model_path: str, confidence: float):
        logger.info("Loading YOLO model path=%s", model_path)
        self.model = YOLO(model_path)
        self.confidence = confidence
        logger.info("YOLO model loaded confidence=%.2f classes=%s", confidence, getattr(self.model, "names", {}))

    def detect(self, frame):
        result = self.model.track(
            frame,
            persist=True,
            conf=self.confidence,
            classes=[0, 2],
            verbose=False,
        )[0]
        if result.boxes is None:
            return []
        detections = []
        for box in result.boxes:
            if box.id is None:
                continue
            coordinates = box.xyxy[0].tolist()
            class_id = int(box.cls[0].item())
            detections.append(
                Detection(
                    track_id=int(box.id[0].item()),
                    class_id=class_id,
                    class_name=self.model.names[class_id],
                    confidence=float(box.conf[0].item()),
                    x1=coordinates[0],
                    y1=coordinates[1],
                    x2=coordinates[2],
                    y2=coordinates[3],
                )
            )
        return detections
