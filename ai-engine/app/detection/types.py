from dataclasses import dataclass


@dataclass
class Detection:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def bottom_center(self):
        return ((self.x1 + self.x2) / 2, self.y2)
