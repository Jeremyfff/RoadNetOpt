import numpy as np
from shapely.geometry import Polygon
import shapely.plotting
from geo import Geometry
from utils.point_utils import xywh2points
from utils import BuildingType
import style_module


class Building(Geometry):
    __all_buildings = set()

    def __init__(self, shell: np.ndarray = None,
                 building_type=BuildingType.NONDEMOLISHABLE):
        super().__init__()
        Geometry.register(self)
        Building.register(self)

        self.shell = shell
        self.polygon = Polygon(shell=self.shell)
        self.building_type = building_type

    def plot(self, *args, **kwargs):
        super(Building, self).plot(*args, **kwargs)
        _style = style_module.get_building_style(self)
        shapely.plotting.plot_polygon(self.polygon, **_style)

    @staticmethod
    def register(obj):
        Building.__all_buildings.add(obj)

    @staticmethod
    def plot_all(*args, **kwargs):
        for building in Building.__all_buildings:
            building.plot(*args, **kwargs)
            
    @staticmethod
    def get_all_buildings():
        return Building.__all_buildings

    @staticmethod
    def quick_buildings():
        building1 = Building(xywh2points(44, 63, 42, 35), building_type=BuildingType.DEMOLISHABLE)
        return [building1]
