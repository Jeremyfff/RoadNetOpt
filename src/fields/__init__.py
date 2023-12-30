from utils import point_utils, FieldOverlayMode


class Field:
    def __init__(self):
        self.overlay_mode = FieldOverlayMode.ADD
        self.weight = 1
        self.name = "Field"
        self.cached_points = None
        self.cached_reward = None

    def update(self):
        pass

    def sample(self, points):
        print(f"Sampling {self.name}")

    def plot(self):
        point_utils.plot_points(self.cached_points, self.cached_reward)

    def cache(self, points, rewards):
        self.cached_points = points
        self.cached_reward = rewards




from fields.building_field import BuildingField
from fields.attraction_field import AttractionField
from fields.direction_field import DirectionField
from fields.momentum_field import MomentumField

