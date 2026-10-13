class IntrusionDetector:
    def __init__(self, zone):
        self.zone = zone
        self.active_tracks = set()

    def check(self, detection):
        x, y = detection.bottom_center
        inside = self.zone.contains(x, y)
        if inside and detection.track_id not in self.active_tracks:
            self.active_tracks.add(detection.track_id)
            return True
        if not inside:
            self.active_tracks.discard(detection.track_id)
        return False
