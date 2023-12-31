from utils import point_utils, FieldOverlayMode


class Field:
    """
    场的基类， 所有的场都应继承这个基类
    """
    def __init__(self):
        self.overlay_mode = FieldOverlayMode.ADD  # 场的叠加方式
        self.weight = 1  # 场的权重
        self.name = "Field"  # 场的名称

        self._cached_points = None  # 缓存的采样点
        self._cached_reward = None  # 缓存的奖励值

    def update(self):
        pass

    def sample(self, points):
        """采样"""
        print(f"Sampling {self.name}")
        self._cached_points = None
        self._cached_reward = None

    def plot(self, show_values=False):
        point_utils.plot_points(points=self._cached_points, values=self._cached_reward, show_values=show_values)

    def cache(self, points, rewards):
        """每次采样结束后调用，用以绘图"""
        self._cached_points = points
        self._cached_reward = rewards


from fields.building_field import BuildingField
from fields.attraction_field import AttractionField
from fields.direction_field import DirectionField
from fields.momentum_field import MomentumField
from fields.random_field import RandomField

