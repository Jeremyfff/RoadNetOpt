from fields import Field, FieldOverlayMode
from geo import Building
from shapely.geometry import Point
import numpy as np


class RandomField(Field):
    """
    随机场
    """
    def __init__(self):
        super().__init__()
        self.overlay_mode = FieldOverlayMode.ADD
        self.name = "RandomField"

    def sample(self, points):
        super(RandomField, self).sample(points)
        rewards = np.random.rand(points.shape[0])
        super(RandomField, self).cache(points, rewards)
        return rewards
