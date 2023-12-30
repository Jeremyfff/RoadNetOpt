import numpy as np
from scipy import interpolate
import shapely.plotting
from shapely.geometry import Polygon, LineString

from geo import Geometry
from utils import RoadLevel, RoadState, BuildingType, point_utils
import style_module


class Road(Geometry):
    all_roads = set()

    def __init__(self, points: np.ndarray = None, level=RoadLevel.MAIN, state=RoadState.RAW):
        super().__init__()
        Geometry.register(self)
        Road.all_roads.add(self)
        self.points = points
        self.level = level
        self.state = state

        self._search_space = None
        self._rewards = None

    def interpolate(self, t):
        distances = np.cumsum(np.sqrt(np.sum(np.diff(self.points, axis=0) ** 2, axis=1)))
        distances = np.insert(distances, 0, 0)
        normalized_distances = distances / distances[-1]
        interp_func = interpolate.interp1d(normalized_distances, self.points, axis=0)

        interpolated_point = interp_func(t)
        return interpolated_point

    def get_last_point(self):
        return self.points[-1]

    def add_point(self, point):
        self.points = np.append(self.points, [point], axis=0)

    def pop_point(self):
        return self.points.pop()

    def get_last_vector(self):
        if self.points is None or self.points.shape[0] < 2:
            return np.array([0, 0])
        else:
            return point_utils.normalize_point(self.points[-1] - self.points[-2])

    def plot(self, *args, **kwargs):
        if self.points.shape[0] < 2:
            return
        super(Road, self).plot(*args, **kwargs)

        _style = style_module.get_road_style(self)
        line = LineString(self.points)
        shapely.plotting.plot_line(line, **_style)

    @staticmethod
    def plot_roads(roads, *args, **kwargs):
        for road in roads:
            road.plot(*args, **kwargs)

    @staticmethod
    def RandomRoads():
        road_points1 = np.array([[0, 0], [0, 100]])
        level1 = RoadLevel.MAIN
        road_points2 = np.array([[-20, 20], [120, 20]])
        level2 = RoadLevel.SECONDARY
        road1 = Road(road_points1, level1)
        road2 = Road(road_points2, level2)

        return [road1, road2]
