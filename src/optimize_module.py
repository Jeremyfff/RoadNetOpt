import numpy as np
from geo.road import Road
from utils import point_utils, FieldOverlayMode


class RoadOptimizer:
    def __init__(self, road, fields):
        self.name = "RoadOptimizer"
        self._target_road: Road = road
        self._fields = fields
        self._search_space = None
        self._rewards = None

    def cluster_fields(self):
        add_fields = []
        mul_fields = []
        for field in self._fields:
            if field.overlay_mode == FieldOverlayMode.ADD:
                add_fields.append(field)
            elif field.overlay_mode == FieldOverlayMode.MUL:
                mul_fields.append(field)
        return add_fields, mul_fields

    def clear_rewards(self):
        self._search_space = None
        self._rewards = None

    def get_rewards(self, search_space):
        assert search_space.shape[0] > 0
        self._search_space = search_space
        add_fields, mul_fields = self.cluster_fields()

        self._rewards = np.zeros((self._search_space.shape[0],))
        for field in add_fields:
            rwd = field.sample(search_space)
            self._rewards += rwd
        for field in mul_fields:
            rwd = field.sample(search_space)
            self._rewards *= rwd

    def step(self):
        assert self._search_space is not None
        assert self._rewards is not None

        max_index = np.argmax(self._rewards)
        self._target_road.add_point(self._search_space[max_index])

        for field in self._fields:
            field.update()

    def plot(self, show_values=False):
        point_utils.plot_points(points=self._search_space, values=self._rewards, show_values=show_values)
