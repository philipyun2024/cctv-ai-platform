import cv2


class CameraStream:
    def __init__(self, url: str):
        self.url = url
        self.capture = None

    def connect(self):
        self.capture = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        if not self.capture.isOpened():
            raise RuntimeError(f"Unable to open video source: {self.url}")

    def read(self):
        if self.capture is None:
            self.connect()
        success, frame = self.capture.read()
        if not success:
            self.reconnect()
            return None
        return frame

    def reconnect(self):
        self.close()
        self.connect()

    def close(self):
        if self.capture:
            self.capture.release()
            self.capture = None
