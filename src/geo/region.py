import ctypes
import logging
import time
from collections import defaultdict
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import shapely.plotting
from geo import Object
from utils.common_utils import timer
from utils.point_utils import xywh2points
from utils import RegionAccessibleType, RegionType, RegionCluster
import pandas as pd
import uuid
from lib.accelerator import cAccelerator, arrs_addr_len


class Region(Object):
    __region_attrs = ['uid', 'geometry', 'coords', 'enabled', 'accessible', 'region_type', 'quality']
    __region_gdf = gpd.GeoDataFrame(columns=__region_attrs)
    __region_gdf.set_index('uid')

    __uid = uuid.uuid4()

    @staticmethod
    def uid():
        return Region.__uid

    # region 增加删除
    @staticmethod
    def _create_region_by_coords(coords: np.ndarray,
                                 accessible: RegionAccessibleType = RegionAccessibleType.UNDEFINED,
                                 region_type: RegionType = RegionType.UNDEFINED,
                                 enabled: bool = True):
        geometry = Polygon(coords)
        uid = uuid.uuid4()
        new_row = {
            'uid': [uid],
            'geometry': [geometry],
            'coords': [coords],
            'accessible': [accessible],
            'region_type': [region_type],
            'enabled': [enabled]
        }
        return gpd.GeoDataFrame(new_row, index=new_row['uid'])

    @staticmethod
    def _create_regions_by_coords(coords_list: list[np.ndarray],
                                  accessible_list: list[RegionAccessibleType] = None,
                                  region_type_list: list[RegionType] = None,
                                  enable_list: list[bool] = None):
        geometry_list = [Polygon(points) for points in coords_list]
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
            'coords': coords_list,
            'accessible': accessible_list,
            'region_type': region_type_list,
            'enabled': enable_list
        }
        return gpd.GeoDataFrame(new_data, index=new_data['uid'])

    @staticmethod
    def add_region(region, return_uid=True):
        if not Region.__region_gdf.empty:
            Region.__region_gdf = gpd.pd.concat([Region.__region_gdf, region], ignore_index=False)
        else:
            Region.__region_gdf = region
        Region.__uid = uuid.uuid4()
        if return_uid:
            return region['uid']

    @staticmethod
    def add_regions(regions, return_uid=False):
        if not Region.__region_gdf.empty:
            Region.__region_gdf = gpd.pd.concat([Region.__region_gdf, regions], ignore_index=False)
        else:
            Region.__region_gdf = regions
        Region.__uid = uuid.uuid4()
        if return_uid:
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
    def add_regions_by_coords(coords_list: list[np.ndarray],
                              accessible_list: list[RegionAccessibleType] = None,
                              region_type_list: list[RegionType] = None,
                              enable_list: list[bool] = None):
        regions = Region._create_regions_by_coords(coords_list,
                                                   accessible_list,
                                                   region_type_list,
                                                   enable_list)
        return Region.add_regions(regions)

    @staticmethod
    def delete_region(region):
        uid = region['uid']
        Region.__region_gdf.drop(uid, inplace=True)
        Region.__uid = uuid.uuid4()

    @staticmethod
    def delete_region_by_uid(uid):
        region = Region.get_region_by_uid(uid)
        Region.delete_region(region)

    @staticmethod
    def delete_all():
        Region.__region_gdf.drop(Region.__region_gdf['uid'], inplace=True)
        Region.__uid = uuid.uuid4()

    # endregion

    # region 获取查找
    @staticmethod
    def get_region_attrs():
        return Region.__region_attrs

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

    @staticmethod
    def get_regions_by_cluster(cluster: RegionCluster):
        cluster = cluster.cluster
        uid_sets_by_attr = []
        for attr in cluster:
            gdfs = []
            if all(cluster[attr].values()):
                print(f'{attr} 全都是True, 跳过')
                continue
            for key in cluster[attr]:
                if cluster[attr][key]:
                    _gdfs = Region.get_regions_by_attr_and_value(attr, key)
                    gdfs.append(_gdfs)
            if len(gdfs) == 0:
                return None
            gdf = pd.concat(gdfs, ignore_index=False)
            uid_sets_by_attr.append(set(gdf.index))
        if len(uid_sets_by_attr) == 0:
            print(f'全都为True, 直接返回所有')
            return Region.get_all_regions()
        common_uid = list(set.intersection(*uid_sets_by_attr))
        return Region.get_all_regions().loc[common_uid]

    # endregion

    # region 编辑修改
    @staticmethod
    def set_attr_value(regions, attr, value):
        # TODO: 这里可能有问题
        assert attr in Region.__region_attrs, f'unexpected attr ({attr}), attr must be one of these: {Region.__region_attrs}'
        regions[attr] = value
        Region.__uid = uuid.uuid4()

    # endregion

    # region 绘图相关
    @staticmethod
    def plot_regions(regions, *args, **kwargs):
        if regions is None:
            return
        regions.plot(*args, **kwargs)

    @staticmethod
    def plot_all(*args, **kwargs):
        Region.__region_gdf.plot(*args, **kwargs)

    @staticmethod
    def plot_using_style_factory(regions, style_factory, *args, **kwargs):
        if regions is None:
            return
        colors, face_color, edge_color, line_width = style_factory(regions)
        regions_copy = regions.copy()
        regions_copy['colors'] = colors
        regions_copy['edge_color'] = edge_color
        regions_copy['line_width'] = line_width
        regions_copy.plot(color=regions_copy['colors'],
                          edgecolor=regions_copy['edge_color'],
                          linewidth=regions_copy['line_width'],
                          *args, **kwargs)

    @staticmethod
    def get_vertices_data(regions, style_factory, debug=False):
        # time logger
        start_time = time.time()
        # colors and width
        params = style_factory(regions)  # tuple( colors and widths)
        colors = np.array(params[0], dtype=np.float32)  # float32
        if colors.shape[1] == 3:
            colors = np.concatenate((colors, np.ones((len(colors), 1), dtype=np.float32)), axis=1)
        in_r, in_g, in_b, in_a = colors[:, 0].copy(), colors[:, 1].copy(), colors[:, 2].copy(), colors[:, 3].copy()

        # coords, first and num
        vertex_coords = regions['coords']  # pandas
        in_first = np.concatenate(([0], np.cumsum(vertex_coords.apply(len).to_numpy()[:-1])), dtype=np.int32)  # int32
        in_num = vertex_coords.apply(len).to_numpy().astype(np.int32)  # int32
        vertex_coords = np.concatenate(vertex_coords.values, axis=0).astype(np.float32)  # (n, 2) float32
        in_x, in_y = vertex_coords[:, 0].copy(), vertex_coords[:, 1].copy()

        # time logger
        logging.debug(f'prepare bytes 消耗时间 = {time.time() - start_time}s')
        start_time = time.time()

        # c# code
        c_params = arrs_addr_len(in_x, in_y, in_first, in_num, in_r, in_g, in_b, in_a)
        buffer = cAccelerator.TriangulatePolygons(*c_params)

        # time logger
        logging.debug(f'c# 代码消耗时间（含数据传输） = {time.time() - start_time}s')
        start_time = time.time()

        # convert to numpy
        vertices = np.frombuffer(bytes(buffer), np.float32).reshape(-1, 6)
        if np.any(np.isnan(vertices)):
            logging.warning("There are NaN values in the vertices array.")

        # time logger
        logging.debug(f'转换为numpy消耗时间 = {time.time() - start_time}s')
        return vertices

    # endregion

    # region 类型转换

    @staticmethod
    def data_to_regions(data: dict):
        assert 'regions' in data, 'invalid data'
        Region.delete_all()

        regions_data = data['regions']
        assert isinstance(regions_data, list)
        coords_list = []
        accessible_list = []
        region_type_list = []

        for bd in regions_data:
            if len(bd['points']) < 4:
                continue
            coords_list.append(np.array(bd['points']))
            accessible_list.append(bd['accessible'])
            if 'region_type' in bd:  # 向前兼容
                region_type_list.append(bd['region_type'])
            else:
                region_type_list.append(bd['type'])
        Region.add_regions_by_coords(coords_list, accessible_list, region_type_list, None)

    @staticmethod
    def regions_to_data(out_data: dict):
        if 'regions' not in out_data:
            out_data['regions'] = []
        for uid, region in Region.get_all_regions().iterrows():
            region_data = {
                'points': region['coords'],
                'region_type': region['region_type'],
                'accessible': region['accessible'],
                'quality': region['quality']
            }
            out_data['regions'].append(region_data)

    # endregion

    # region 其他

    # endregion


if __name__ == "__main__":
    raise NotImplementedError
