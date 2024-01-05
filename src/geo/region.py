from collections import defaultdict
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import shapely.plotting
from geo import Object
from utils.point_utils import xywh2points
from utils import RegionAccessibleType, RegionType
import uuid


class Region(Object):
    __region_attrs = ['uid', 'geometry', 'enabled', 'accessible', 'region_type', 'quality']
    __region_gdf = gpd.GeoDataFrame(columns=__region_attrs)
    __region_gdf.set_index('uid')

    # region 增加删除
    @staticmethod
    def _create_region_by_coords(coords: np.ndarray,
                                 accessible: RegionAccessibleType = RegionAccessibleType.UNDEFINED,
                                 region_type: RegionType = RegionType.UNDEFINED,
                                 enabled: bool = True):
        geometry = Polygon(coords)
        return Region._create_region_by_geometry(geometry, accessible, region_type, enabled)

    @staticmethod
    def _create_region_by_geometry(geometry: Polygon,
                                   accessible: RegionAccessibleType = RegionAccessibleType.UNDEFINED,
                                   region_type: RegionType = RegionType.UNDEFINED,
                                   enabled: bool = True):
        uid = uuid.uuid4()
        new_row = {
            'uid': [uid],
            'geometry': [geometry],
            'accessible': [accessible],
            'region_type': [region_type],
            'enabled': [enabled]
        }
        return gpd.GeoDataFrame(new_row, index=new_row['uid'])

    @staticmethod
    def _create_regions_by_coords(points_list: list[np.ndarray],
                                  accessible_list: list[RegionAccessibleType] = None,
                                  region_type_list: list[RegionType] = None,
                                  enable_list: list[bool] = None):
        geometry_list = [Polygon(points) for points in points_list]
        return Region._create_regions_by_geometries(geometry_list, accessible_list, region_type_list,
                                                    enable_list)

    @staticmethod
    def _create_regions_by_geometries(geometry_list: list[Polygon],
                                      accessible_list: list[RegionAccessibleType] = None,
                                      region_type_list: list[RegionType] = None,
                                      enable_list: list[bool] = None):

        if enable_list is None:
            enable_list = [True for _ in geometry_list]
        if accessible_list is None:
            accessible_list = [RegionAccessibleType.UNDEFINED for _ in geometry_list]
        if region_type_list is None:
            region_type_list = [RegionType.UNDEFINED for _ in geometry_list]
        assert len(geometry_list) == len(accessible_list) == len(region_type_list)
        uid_list = [uuid.uuid4() for _ in geometry_list]
        new_data = {
            'uid': uid_list,
            'geometry': geometry_list,
            'accessible': accessible_list,
            'region_type': region_type_list,
            'enabled': enable_list
        }
        return gpd.GeoDataFrame(new_data, index=new_data['uid'])

    @staticmethod
    def add_region(region):
        if not Region.__region_gdf.empty:
            Region.__region_gdf = gpd.pd.concat([Region.__region_gdf, region], ignore_index=False)
        else:
            Region.__region_gdf = region
        return region['uid']

    @staticmethod
    def add_regions(regions):
        if not Region.__region_gdf.empty:
            Region.__region_gdf = gpd.pd.concat([Region.__region_gdf, regions], ignore_index=False)
        else:
            Region.__region_gdf = regions
        return list(regions['uid'])

    @staticmethod
    def add_region_by_coords(coords: np.ndarray,
                             accessible: RegionAccessibleType = RegionAccessibleType.UNDEFINED,
                             region_type: RegionType = RegionType.UNDEFINED,
                             enabled: bool = True):
        region = Region._create_region_by_coords(coords,
                                                 accessible,
                                                 region_type,
                                                 enabled)
        return Region.add_region(region)

    @staticmethod
    def add_region_by_geometry(geometry: Polygon,
                               accessible: RegionAccessibleType = RegionAccessibleType.UNDEFINED,
                               region_type: RegionType = RegionType.UNDEFINED,
                               enabled: bool = True):
        region = Region._create_region_by_geometry(geometry,
                                                   accessible,
                                                   region_type,
                                                   enabled)
        return Region.add_region(region)

    @staticmethod
    def add_regions_by_coords(points_list: list[np.ndarray],
                              accessible_list: list[RegionAccessibleType] = None,
                              region_type_list: list[RegionType] = None,
                              enable_list: list[bool] = None):
        regions = Region._create_regions_by_coords(points_list,
                                                   accessible_list,
                                                   region_type_list,
                                                   enable_list)
        return Region.add_regions(regions)

    @staticmethod
    def add_regions_by_geometries(geometry_list: list[Polygon],
                                  accessible_list: list[RegionAccessibleType] = None,
                                  region_type_list: list[RegionType] = None,
                                  enable_list: list[bool] = None):
        regions = Region._create_regions_by_geometries(geometry_list,
                                                       accessible_list,
                                                       region_type_list,
                                                       enable_list)
        return Region.add_regions(regions)

    @staticmethod
    def delete_region(region):
        uid = region['uid']
        Region.__region_gdf.drop(uid, inplace=True)

    @staticmethod
    def delete_region_by_uid(uid):
        region = Region.get_region_by_uid(uid)
        Region.delete_region(region)

    @staticmethod
    def delete_all():
        Region.__region_gdf.drop(Region.__region_gdf['uid'], inplace=True)

    # endregion

    # region 获取查找
    @staticmethod
    def get_region_by_uid(uid):
        region = Region.__region_gdf.loc[uid]
        return region

    @staticmethod
    def get_region_by_index(idx):
        region = Region.__region_gdf.iloc[idx]
        return region

    @staticmethod
    def get_regions_by_attr_and_value(attr: str, value: any):
        assert attr in Region.__region_attrs, f'unexpected attr ({attr}), attr must be one of these: {Region.__region_attrs}'
        regions = Region.__region_gdf.loc[Region.__region_gdf[attr] == value]
        return regions

    @staticmethod
    def get_first_region():
        return Region.get_region_by_index(0)

    @staticmethod
    def get_last_region():
        return Region.get_region_by_index(-1)

    @staticmethod
    def get_all_regions():
        return Region.__region_gdf

    # endregion

    # region 编辑修改
    @staticmethod
    def set_attr_value(regions, attr, value):
        assert attr in Region.__region_attrs, f'unexpected attr ({attr}), attr must be one of these: {Region.__region_attrs}'
        regions[attr] = value

    # endregion

    # region 绘图相关
    @staticmethod
    def plot_regions(regions, *args, **kwargs):
        regions.plot(*args, **kwargs)

    @staticmethod
    def plot_all(*args, **kwargs):
        Region.__region_gdf.plot(*args, **kwargs)

    # endregion

    # region 类型转换

    @staticmethod
    def data_to_regions(data: dict):
        assert 'regions' in data, 'invalid data'
        Region.delete_all()

        regions_data = data['regions']
        points_list = []
        accessible_list = []
        region_type_list = []

        for bd in regions_data:
            if len(bd['points']) < 4:
                continue
            points_list.append(np.array(bd['points']))
            accessible_list.append(bd['accessible'])
            if 'region_type' in bd:  # 向前兼容
                region_type_list.append(bd['region_type'])
            else:
                region_type_list.append(bd['type'])
        Region.add_regions_by_coords(points_list, accessible_list, region_type_list, None)

    @staticmethod
    def regions_to_data(out_data: dict):
        if 'regions' not in out_data:
            out_data['regions'] = []
        for uid, region in Region.get_all_regions().iterrows():
            region_data = {
                'points': np.array(list(region['geometry'].coords)),
                'region_type': region['region_type'],
                'accessible': region['accessible'],
                'quality': region['quality']
            }
            out_data['regions'].append(region_data)

    # endregion

    # region 其他
    @staticmethod
    def quick_regions():
        points = xywh2points(44, 63, 100, 80)
        uid = Region.add_region_by_coords(points,
                                          accessible=RegionAccessibleType.UNDEFINED,
                                          region_type=RegionType.UNDEFINED,
                                          enabled=True
                                          )

        return [uid]
    # endregion


if __name__ == "__main__":
    raise NotImplementedError
