from fields import Field, FieldOverlayMode
from utils import field_utils

import numpy as np
class AttractionField(Field):
    """
    吸引场
    range : 0 ~ 1
    """
    def __init__(self, attractive_points):
        super().__init__()
        self.attractive_points = attractive_points
        self.overlay_mode = FieldOverlayMode.ADD
        self.name = "AttractionField"

    def sample(self, points):
        super(AttractionField, self).sample(points)
        distance_field = field_utils.distance_field(points, self.attractive_points)
        distance_field = field_utils.normalize_field(distance_field)
        rewards = 1 - distance_field
        super().cache(points, rewards)
        return rewards

