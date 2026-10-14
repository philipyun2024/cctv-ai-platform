import logging

import cv2

logger = logging.getLogger(__name__)


class CameraStream:
    def __init__(self, url: str, camera_name: str = "unknown"):
        self.url = url
        self.camera_name = camera_name
        self.capture = None
        self.read_failures = 0

    def connect(self):
        logger.info("Connecting to camera stream camera=%s", self.camera_name)
        self.capture = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        if not self.capture.isOpened():
            logger.error("Unable to open camera stream camera=%s", self.camera_name)
            self.close()
            raise RuntimeError(f"Unable to open video stream for camera: {self.camera_name}")
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        logger.info("Camera stream connected camera=%s width=%s height=%s fps=%.2f", self.camera_name, width, height, fps)
        self.read_failures = 0

    def read(self):
        if self.capture is None:
            self.connect()
        success, frame = self.capture.read()
        if not success or frame is None:
            self.read_failures += 1
            if self.read_failures == 1 or self.read_failures % 30 == 0:
                logger.warning("Camera frame read failed camera=%s consecutive_failures=%s", self.camera_name, self.read_failures)
            self.reconnect()
            return None
        if self.read_failures:
            logger.info("Camera stream recovered camera=%s", self.camera_name)
            self.read_failures = 0
        return frame

    def reconnect(self):
        self.close()
        try:
            self.connect()
        except Exception:
            logger.exception("Camera reconnect failed camera=%s", self.camera_name)

    def close(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
