import time


class LoiteringDetector:
    def __init__(self, zone, threshold_seconds):
        self.zone = zone
        self.threshold_seconds = threshold_seconds
        self.tracks = {}

    def check(self, detection):
        x, y = detection.bottom_center
        if not self.zone.contains(x, y):
            self.tracks.pop(detection.track_id, None)
            return None
        state = self.tracks.setdefault(
            detection.track_id,
            {"started_at": time.monotonic(), "alarm_sent": False},
        )
        elapsed = time.monotonic() - state["started_at"]
        if elapsed >= self.threshold_seconds and not state["alarm_sent"]:
            state["alarm_sent"] = True
            return {"duration": elapsed}
        return None
