import math

from fields import Field, FieldOverlayMode
from geo import Building, Road
from utils import RoadState, polyline_utils, point_utils, common_utils, field_utils
import numpy as np


class MomentumField(Field):
    """
    动量场
    """

    def __init__(self):
        super().__init__()
        self.overlay_mode = FieldOverlayMode.MUL
        self.name = "MomentumField"

    def sample(self, points):
        super(MomentumField, self).sample(points)

        # TODO 性能优化
        optimizing_road = None
        roads = Road.get_all_roads()
        for road in roads:
            if road.state == RoadState.OPTIMIZING:
                optimizing_road = road
                break
        assert optimizing_road is not None, "Failed to find any road in optimizing state. Please check if you assign " \
                                            "road state correctly when creating roads "

        last_vector = optimizing_road.get_last_vector()
        if math.sqrt(last_vector[0] ** 2 + last_vector[1] ** 2) == 0:
            last_vector = np.array([1, 1])
        assert optimizing_road.points is not None and optimizing_road.points.shape[0] > 0
        last_point = optimizing_road.points[-1]
        vec = points - last_point
        n_vec = point_utils.normalize_vectors(vec)
        a = np.dot(n_vec, last_vector)
        a = field_utils.normalize_field(a)
        b = common_utils.gaussian(a, 1.0, 0.1)
        b = field_utils.normalize_field(b)
        c = common_utils.gaussian(a, 0.5, 0.1)
        c = field_utils.normalize_field(c)
        d = np.power(field_utils.normalize_field(np.clip(1 - np.linalg.norm(vec, axis=1) / 40, 0, None)), 0.3)

        rewards = field_utils.normalize_field((b + c) * d)
        rewards = np.clip(rewards, 0, 1)
        super().cache(points, rewards)
        return rewards
