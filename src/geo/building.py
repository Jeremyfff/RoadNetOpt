import numpy as np
from shapely.geometry import Polygon
import shapely.plotting


from geo import Geometry
from utils.point_utils import xywh2points
from utils import BuildingType
import style_module


class Building(Geometry):
    all_buildings = set()

    def __init__(self, shell: np.ndarray = None,
                 building_type=BuildingType.NONDEMOLISHABLE):
        super().__init__()
        Geometry.register(self)
        Building.all_buildings.add(self)
        self.shell = shell

        self.polygon = Polygon(shell=self.shell)
        self.building_type = building_type

    def plot(self, *args, **kwargs):
        super(Building, self).plot(*args, **kwargs)
        _style = style_module.get_building_style(self)
        shapely.plotting.plot_polygon(self.polygon, **_style)

    @staticmethod
    def plot_buildings(buildings, *args, **kwargs):
        for building in buildings:
            building.plot(*args, **kwargs)

    @staticmethod
    def RandomBuildings():
        building1 = Building(xywh2points(44, 63, 42, 35), building_type=BuildingType.DEMOLISHABLE)
        return [building1]
