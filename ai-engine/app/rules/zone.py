from shapely.geometry import Point, Polygon


class Zone:
    """Polygon zone using normalized 0..1 coordinates."""

    def __init__(self, zone_id, name, points, frame_width, frame_height):
        self.zone_id = zone_id
        self.name = name
        pixel_points = [
            (point[0] * frame_width, point[1] * frame_height)
            for point in points
        ]
        self.polygon = Polygon(pixel_points)

    def contains(self, x, y):
        return self.polygon.contains(Point(x, y))
