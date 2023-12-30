from fields import Field, FieldOverlayMode
from geo import Building
from shapely.geometry import Point
import numpy as np


class BuildingField(Field):
    """
    Inside : 0
    Outsize : 1
    """
    def __init__(self):
        super().__init__()
        self.overlay_mode = FieldOverlayMode.MUL
        self.name = "BuildingField"

    def sample(self, points):
        super(BuildingField, self).sample(points)
        shapely_points = [Point(x, y) for x, y in points]
        shapely_polygons = [building.polygon for building in Building.all_buildings]

        # TODO 优化
        is_inside = [float(any(point.within(poly) for poly in shapely_polygons)) for point in shapely_points]
        rewards = 1 - np.array(is_inside)
        super().cache(points, rewards)
        return rewards
