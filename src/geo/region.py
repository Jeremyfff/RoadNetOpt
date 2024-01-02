from collections import defaultdict

import numpy as np
from shapely.geometry import Polygon
import shapely.plotting
from geo import Object
from utils.point_utils import xywh2points
from utils import RegionAccessibleType, RegionType
import style_module


class Region(Object):
    __all_regions = set()
    __region_cluster = {'accessible': defaultdict(set), 'type': defaultdict(set)}
    __region_geo_cluster = {'accessible': defaultdict(list), 'type': defaultdict(list)}

    def __init__(self, shell: np.ndarray = None,
                 accessible=RegionAccessibleType.UNDEFINED,
                 region_type=RegionType.UNDEFINED):
        super().__init__()

        self.shell = shell
        self.polygon = Polygon(shell=self.shell)
        self.accessible = accessible
        self.region_type = region_type
        Region.register(self)

    def plot(self, by='accessible', *args, **kwargs):
        super(Region, self).plot(*args, **kwargs)
        _style = style_module.get_region_plot_style(self, by=by)
        shapely.plotting.plot_polygon(self.polygon, **_style)

    @staticmethod
    def register(obj):
        Region.__all_regions.add(obj)
        Region.__region_cluster['accessible'][obj.accessible].add(obj)
        Region.__region_cluster['type'][obj.region_type].add(obj)
    @staticmethod
    def re_register_all():
        regions = Region.get_all_regions()
        Region.delete_all_regions()
        for region in regions:
            Region.register(region)
    @staticmethod
    def delete_all_regions():
        Region.__all_regions = set()
        __region_cluster = {'accessible': defaultdict(set), 'type': defaultdict(set)}
        __region_geo_cluster = {'accessible': defaultdict(list), 'type': defaultdict(list)}
    @staticmethod
    def plot_all(by='accessible', *args, **kwargs):
        for region in Region.__all_regions:
            region.plot(by, *args, **kwargs)

    @staticmethod
    def get_all_regions():
        return Region.__all_regions



    @staticmethod
    def quick_regions():
        raise NotImplementedError

    @staticmethod
    def data_to_regions(data: dict):
        assert 'regions' in data, 'invalid data'
        regions = []
        regions_data = data['regions']
        for rg in regions_data:
            region = Region(shell=np.array(rg['points']),
                            accessible=rg['accessible'],
                            region_type=rg['type'])
            regions.append(region)
        return regions

    @staticmethod
    def regions_to_data(out_data: dict):
        if 'regions' not in out_data:
            out_data['regions'] = []
        for region in Region.get_all_regions():
            region_data = {
                'points': region.shell.tolist(),
                'accessible': region.accessible,
                'type': region.region_type
            }
            out_data['regions'].append(region_data)


if __name__ == "__main__":
    raise NotImplementedError
