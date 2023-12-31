from shapely.geometry import Point, Polygon
import numpy as np
from scipy.interpolate import interp1d
from fields import Field, FieldOverlayMode
from geo import Building, Road
from utils import RoadState, polyline_utils, field_utils, point_utils


class DirectionField(Field):
    """
    垂直梯度的方向场
    """

    def __init__(self):
        super().__init__()
        self.overlay_mode = FieldOverlayMode.ADD
        self.name = "DirectionField"

    def sample(self, points):
        super(DirectionField, self).sample(points)

        # TODO 大量性能优化， 计算正确性校验
        buildings = Building.get_all_buildings()
        roads = Road.get_all_roads()
        all_points = []
        optimizing_road = None
        for road in roads:
            if road.state == RoadState.OPTIMIZING:
                optimizing_road = road
                continue
            new_points = polyline_utils.interpolate_by_distance(road.points, 5)
            all_points.append(new_points)
        assert optimizing_road is not None, "Failed to find any road in optimizing state. Please check if you assign " \
                                            "road state correctly when creating roads "
        for building in buildings:
            bound_pts = polyline_utils.get_closed_polyline(building.shell)
            new_points = polyline_utils.interpolate_by_distance(bound_pts, 5)
            all_points.append(new_points)
        point_cloud = np.vstack(all_points)
        print(f"DirectionField point_cloud.shape = {point_cloud.shape}")

        x_offset_points = point_utils.offset_points(points, np.array([0.1, 0]))
        y_offset_points = point_utils.offset_points(points, np.array([0, 0.1]))

        distance_field = field_utils.distance_field(points, point_cloud)

        x_offset_distance_field = field_utils.distance_field(x_offset_points, point_cloud)
        y_offset_distance_field = field_utils.distance_field(y_offset_points, point_cloud)

        x_delta = x_offset_distance_field - distance_field
        y_delta = y_offset_distance_field - distance_field

        grad = point_utils.normalize_vectors(np.stack((x_delta, y_delta), axis=1))
        v_grad = point_utils.v_rotate_vectors(grad)
        last_vec = optimizing_road.get_last_vector()
        rewards = np.abs(np.dot(v_grad, last_vec))
        rewards = 2 * field_utils.normalize_field(rewards) - 1
        rewards = np.clip(rewards, 0, 1)
        super().cache(points, rewards)
        return rewards
