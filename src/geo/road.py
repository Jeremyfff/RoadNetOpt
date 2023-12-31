import numpy as np

import shapely.plotting
from shapely.geometry import Polygon, LineString

from geo import Geometry
from utils import RoadLevel, RoadState, BuildingType, point_utils, polyline_utils
import style_module


class Road(Geometry):
    __all_roads = set()

    def __init__(self, points: np.ndarray = None, level=RoadLevel.MAIN, state=RoadState.RAW):
        super().__init__()
        Geometry.register(self)
        Road.register(self)
        self.points = points
        self.level = level
        self.state = state

        self._search_space = None
        self._rewards = None

    def plot(self, *args, **kwargs):
        if self.points.shape[0] < 2:
            return
        super(Road, self).plot(*args, **kwargs)

        _style = style_module.get_road_style(self)
        line = LineString(self.points)
        shapely.plotting.plot_line(line, **_style)

    def add_point(self, point):
        self.points = np.append(self.points, [point], axis=0)

    def pop_point(self):
        return self.points.pop()

    def get_last_point(self):
        return self.points[-1]

    def get_last_vector(self):
        if self.points is None or self.points.shape[0] < 2:
            return np.array([0, 0])
        else:
            return point_utils.normalize_vector(self.points[-1] - self.points[-2])

    def interpolate(self, t):
        return polyline_utils.interpolate_by_t(self.points, t)
    
    @staticmethod
    def register(obj):
        Road.__all_roads.add(obj)

    @staticmethod
    def plot_all(*args, **kwargs):
        for road in Road.__all_roads:
            road.plot(*args, **kwargs)

    @staticmethod
    def get_all_roads():
        return Road.__all_roads

    @staticmethod
    def quick_roads():
        road_points1 = np.array([[0, 0], [0, 100]])
        level1 = RoadLevel.MAIN
        road_points2 = np.array([[-20, 20], [120, 20]])
        level2 = RoadLevel.SECONDARY
        road1 = Road(road_points1, level1)
        road2 = Road(road_points2, level2)

        return [road1, road2]