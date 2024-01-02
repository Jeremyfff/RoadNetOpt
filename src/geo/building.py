from collections import defaultdict
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import shapely.plotting
from geo import Object
from utils.point_utils import xywh2points
from utils import BuildingMovableType, BuildingStyle, BuildingQuality
import style_module


class Building(Object):
    __all_buildings = set()
    __building_cluster = {'movable': defaultdict(set), 'style': defaultdict(set), 'quality': defaultdict(set)}
    __building_geo_cluster = {'movable': defaultdict(list), 'style': defaultdict(list), 'quality': defaultdict(list)}
    def __init__(self, shell: np.ndarray = None,
                 movable=BuildingMovableType.UNDEFINED,
                 style=BuildingStyle.UNDEFINED,
                 quality=BuildingQuality.UNDEFINED):
        super().__init__()

        self.shell = shell
        self.polygon = Polygon(shell=self.shell)
        self.movable = movable
        self.style = style
        self.quality = quality

        Building.register(self)

    def plot(self, by='movable', *args, **kwargs):
        super(Building, self).plot(*args, **kwargs)
        _style = style_module.get_building_plot_style(self, by=by)
        shapely.plotting.plot_polygon(self.polygon, **_style)

    @staticmethod
    def register(obj):
        Building.__all_buildings.add(obj)
        Building.__building_cluster['movable'][obj.movable].add(obj)
        Building.__building_cluster['style'][obj.style].add(obj)
        Building.__building_cluster['quality'][obj.quality].add(obj)
        Building.__building_geo_cluster['movable'][obj.movable].append(obj.polygon)
        Building.__building_geo_cluster['style'][obj.style].append(obj.polygon)
        Building.__building_geo_cluster['quality'][obj.quality].append(obj.polygon)

    @staticmethod
    def re_register_all():
        buildings = Building.get_all_buildings()
        Building.delete_all_buildings()
        for building in buildings:
            Building.register(building)

    @staticmethod
    def delete_all_buildings():
        Building.__all_buildings = set()
        __building_cluster = {'movable': defaultdict(set), 'style': defaultdict(set), 'quality': defaultdict(set)}
        __building_geo_cluster = {'movable': defaultdict(set), 'style': defaultdict(set), 'quality': defaultdict(set)}
    @staticmethod
    def plot_all(by='movable', *args, **kwargs):
        for key in Building.__building_cluster[by]:
            print(key)
            print(len(Building.__building_cluster[by][key]) )
            if len(Building.__building_cluster[by][key]) == 0:
                continue
            buildings = Building.__building_cluster[by][key]
            building_geos = Building.__building_geo_cluster[by][key]
            _style = style_module.get_building_plot_style(next(iter(buildings)), by=by)
            gpd.GeoSeries(list(building_geos)).plot(*args, **kwargs, **_style)

    @staticmethod
    def get_all_buildings():
        return Building.__all_buildings

    @staticmethod
    def quick_buildings():

        building1 = Building(xywh2points(44, 63, 42, 35),
                             movable=BuildingMovableType.DEMOLISHABLE,
                             quality=BuildingQuality.GOOD,
                             style=BuildingStyle.NORMAL)
        return [building1]

    @staticmethod
    def data_to_buildings(data: dict):
        assert 'buildings' in data, 'invalid data'
        buildings = []
        buildings_data = data['buildings']
        for bd in buildings_data:
            if len(bd['points']) < 4:
                continue
            building = Building(shell=np.array(bd['points']),
                                style=bd['style'],
                                movable=bd['movable'],
                                quality=bd['quality'])
            buildings.append(building)
        return buildings

    @staticmethod
    def buildings_to_data(out_data: dict):
        if 'buildings' not in out_data:
            out_data['buildings'] = []
        for building in Building.get_all_buildings():
            building_data = {
                'points': building.shell.tolist(),
                'style': building.style,
                'movable': building.movable,
                'quality': building.quality
            }
            out_data['buildings'].append(building_data)


if __name__ == "__main__":
    from geo import Road
    import matplotlib.pyplot as plt

    roads = Road.quick_roads()
    buildings = Building.quick_buildings()
    Object.plot_all()

    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()
    plt.show()
