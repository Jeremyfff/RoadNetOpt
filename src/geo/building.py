import traceback
import uuid
from collections import defaultdict
import geopandas as gpd
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as PolygonPatch
from shapely.geometry import Polygon
import shapely.plotting
from tqdm import tqdm
from numba import jit, typed
import pandas as pd
from geo import Object
from utils.common_utils import timer
from utils.point_utils import xywh2points
from utils import BuildingMovableType, BuildingStyle, BuildingQuality, BuildingCluster
import style_module

print('building loaded')
class Building(Object):
    __building_attrs = ['uid', 'geometry', 'enabled', 'movable', 'style', 'quality', 'patch']
    __building_gdf = gpd.GeoDataFrame(columns=__building_attrs)
    __building_gdf.set_index('uid')

    __uid = uuid.uuid4()


    @staticmethod
    def uid():
        return Building.__uid

    # region 增加删除
    @staticmethod
    def _create_building_by_coords(coords: np.ndarray,
                                   movable: BuildingMovableType = BuildingMovableType.UNDEFINED,
                                   style: BuildingStyle = BuildingStyle.UNDEFINED,
                                   quality: BuildingQuality = BuildingQuality.UNDEFINED,
                                   enabled: bool = True):
        geometry = Polygon(coords)
        return Building._create_building_by_geometry(geometry, movable, style, quality, enabled)

    @staticmethod
    def _create_building_by_geometry(geometry: Polygon,
                                     movable: BuildingMovableType = BuildingMovableType.UNDEFINED,
                                     style: BuildingStyle = BuildingStyle.UNDEFINED,
                                     quality: BuildingQuality = BuildingQuality.UNDEFINED,
                                     enabled: bool = True):
        uid = uuid.uuid4()
        patch = PolygonPatch(np.asarray(geometry.exterior.coords))
        new_row = {
            'uid': [uid],
            'geometry': [geometry],
            'movable': [movable],
            'style': [style],
            'quality': [quality],
            'enabled': [enabled],
            'patch': [patch]
        }
        return gpd.GeoDataFrame(new_row, index=new_row['uid'])

    @staticmethod
    def _create_buildings_by_coords(points_list: list[np.ndarray],
                                    movable_list: list[BuildingMovableType] = None,
                                    style_list: list[BuildingStyle] = None,
                                    quality_list: list[BuildingQuality] = None,
                                    enable_list: list[bool] = None):
        geometry_list = [Polygon(points) for points in points_list]
        return Building._create_buildings_by_geometries(geometry_list, movable_list, style_list, quality_list,
                                                        enable_list)

    @staticmethod
    def _create_buildings_by_geometries(geometry_list: list[Polygon],
                                        movable_list: list[BuildingMovableType] = None,
                                        style_list: list[BuildingStyle] = None,
                                        quality_list: list[BuildingQuality] = None,
                                        enable_list: list[bool] = None):

        if enable_list is None:
            enable_list = [True for _ in geometry_list]
        if movable_list is None:
            movable_list = [BuildingMovableType.UNDEFINED for _ in geometry_list]
        if style_list is None:
            style_list = [BuildingStyle.UNDEFINED for _ in geometry_list]
        if quality_list is None:
            quality_list = [BuildingQuality.UNDEFINED for _ in geometry_list]
        assert len(geometry_list) == len(movable_list) == len(style_list) == len(quality_list)
        uid_list = [uuid.uuid4() for _ in geometry_list]
        patch_list = [PolygonPatch(np.asarray(geometry.exterior.coords)) for geometry in geometry_list]
        new_data = {
            'uid': uid_list,
            'geometry': geometry_list,
            'movable': movable_list,
            'style': style_list,
            'quality': quality_list,
            'enabled': enable_list,
            'patch': patch_list
        }
        return gpd.GeoDataFrame(new_data, index=new_data['uid'])

    @staticmethod
    def add_building(building):
        if not Building.__building_gdf.empty:
            Building.__building_gdf = gpd.pd.concat([Building.__building_gdf, building], ignore_index=False)
        else:
            Building.__building_gdf = building
        Building.__uid = uuid.uuid4()
        return building['uid']

    @staticmethod
    def add_buildings(buildings):
        if not Building.__building_gdf.empty:
            Building.__building_gdf = gpd.pd.concat([Building.__building_gdf, buildings], ignore_index=False)
        else:
            Building.__building_gdf = buildings
        Building.__uid = uuid.uuid4()
        return list(buildings['uid'])

    @staticmethod
    def add_building_by_coords(coords: np.ndarray,
                               movable: BuildingMovableType = BuildingMovableType.UNDEFINED,
                               style: BuildingStyle = BuildingStyle.UNDEFINED,
                               quality: BuildingQuality = BuildingQuality.UNDEFINED,
                               enabled: bool = True):
        building = Building._create_building_by_coords(coords,
                                                       movable,
                                                       style,
                                                       quality,
                                                       enabled)
        return Building.add_building(building)

    @staticmethod
    def add_building_by_geometry(geometry: Polygon,
                                 movable: BuildingMovableType = BuildingMovableType.UNDEFINED,
                                 style: BuildingStyle = BuildingStyle.UNDEFINED,
                                 quality: BuildingQuality = BuildingQuality.UNDEFINED,
                                 enabled: bool = True):
        building = Building._create_building_by_geometry(geometry,
                                                         movable,
                                                         style,
                                                         quality,
                                                         enabled)
        return Building.add_building(building)

    @staticmethod
    def add_buildings_by_coords(points_list: list[np.ndarray],
                                movable_list: list[BuildingMovableType] = None,
                                style_list: list[BuildingStyle] = None,
                                quality_list: list[BuildingQuality] = None,
                                enable_list: list[bool] = None):
        buildings = Building._create_buildings_by_coords(points_list,
                                                         movable_list,
                                                         style_list,
                                                         quality_list,
                                                         enable_list)
        return Building.add_buildings(buildings)

    @staticmethod
    def add_buildings_by_geometries(geometry_list: list[Polygon],
                                    movable_list: list[BuildingMovableType] = None,
                                    style_list: list[BuildingStyle] = None,
                                    quality_list: list[BuildingQuality] = None,
                                    enable_list: list[bool] = None):
        buildings = Building._create_buildings_by_geometries(geometry_list,
                                                             movable_list,
                                                             style_list,
                                                             quality_list,
                                                             enable_list)
        return Building.add_buildings(buildings)

    @staticmethod
    def delete_building(building):
        uid = building['uid']
        Building.__building_gdf.drop(uid, inplace=True)
        Building.__uid = uuid.uuid4()

    @staticmethod
    def delete_building_by_uid(uid):
        building = Building.get_building_by_uid(uid)
        Building.delete_building(building)

    @staticmethod
    def delete_all():
        Building.__building_gdf.drop(Building.__building_gdf['uid'], inplace=True)
        Building.__uid = uuid.uuid4()

    # endregion

    # region 获取查找
    @staticmethod
    def get_building_attrs():
        return Building.__building_attrs

    @staticmethod
    def get_building_by_uid(uid):
        building = Building.__building_gdf.loc[uid]
        return building

    @staticmethod
    def get_building_by_index(idx):
        building = Building.__building_gdf.iloc[idx]
        return building

    @staticmethod
    def get_buildings_by_attr_and_value(attr: str, value: any):
        assert attr in Building.__building_attrs, f'unexpected attr ({attr}), attr must be one of these: {Building.__building_attrs}'
        buildings = Building.__building_gdf.loc[Building.__building_gdf[attr] == value]
        return buildings

    @staticmethod
    def get_first_building():
        return Building.get_building_by_index(0)

    @staticmethod
    def get_last_building():
        return Building.get_building_by_index(-1)

    @staticmethod
    def get_all_buildings():
        return Building.__building_gdf

    @staticmethod
    def get_buildings_by_cluster(cluster: BuildingCluster):
        cluster = cluster.cluster
        uid_sets_by_attr = []
        for attr in cluster:
            gdfs = []
            if all(cluster[attr].values()):
                print(f'{attr} 全都是True, 跳过')
                continue
            for key in cluster[attr]:
                if cluster[attr][key]:
                    _gdfs = Building.get_buildings_by_attr_and_value(attr, key)
                    gdfs.append(_gdfs)
            if len(gdfs) == 0:
                return None
            gdf = pd.concat(gdfs, ignore_index=False)
            uid_sets_by_attr.append(set(gdf.index))
        if len(uid_sets_by_attr) == 0:
            print(f'全都为True, 直接返回所有')
            return Building.get_all_buildings()
        common_uid = list(set.intersection(*uid_sets_by_attr))
        return Building.get_all_buildings().loc[common_uid]

    # endregion

    # region 编辑修改
    @staticmethod
    def set_attr_value(buildings, attr, value):
        # TODO 这个可能有问题
        assert attr in Building.__building_attrs, f'unexpected attr ({attr}), attr must be one of these: {Building.__building_attrs}'
        buildings[attr] = value
        Building.__uid = uuid.uuid4()

    # endregion

    # region 绘图相关
    @staticmethod
    def plot_buildings(buildings, *args, **kwargs):
        if buildings is None:
            return
        buildings.plot(*args, **kwargs)

    @staticmethod
    def plot_all(*args, **kwargs):
        Building.__building_gdf.plot(*args, **kwargs)

    @staticmethod
    def plot_using_style_factory(buildings, style_factory, *args, **kwargs):
        if buildings is None:
            return
        colors, face_color, edge_color, line_width = style_factory(buildings)
        buildings_copy = buildings.copy()
        buildings_copy['colors'] = colors
        buildings_copy['edge_color'] = edge_color
        buildings_copy['line_width'] = line_width
        buildings_copy.plot(color=buildings_copy['colors'],
                            edgecolor=buildings_copy['edge_color'],
                            linewidth=buildings_copy['line_width'],
                            *args, **kwargs)


    @staticmethod
    def plot_patch_using_style_factory(buildings, style_factory, *args, **kwargs):
        ax = kwargs['ax']
        kwargs.pop('ax')
        colors, face_color, edge_color, line_width = style_factory(buildings)
        patches = buildings['patch'].tolist()
        pc = PatchCollection(patches, facecolor=face_color, linewidth=line_width, edgecolor=edge_color, *args, **kwargs)
        ax.add_collection(pc, autolim=True)
        return pc

    # endregion

    # region 类型转换

    @staticmethod
    @timer
    def data_to_buildings(data: dict):
        assert 'buildings' in data, 'invalid data'
        Building.delete_all()

        buildings_data = data['buildings']
        assert isinstance(buildings_data, list)
        print(f"共有{len(buildings_data)}条建筑数据")
        points_list = []
        movable_list = []
        style_list = []
        quality_list = []
        for i in tqdm(range(len(buildings_data))):
            bd = buildings_data[i]
            if len(bd['points']) < 4:
                continue
            points_list.append(np.array(bd['points']))
            movable_list.append(bd['movable'])
            style_list.append(bd['style'])
            quality_list.append(bd['quality'])
        Building.add_buildings_by_coords(points_list, movable_list, style_list, quality_list, None)

    @staticmethod
    def buildings_to_data(out_data: dict):
        if 'buildings' not in out_data:
            out_data['buildings'] = []
        for uid, building in Building.get_all_buildings().iterrows():
            building_data = {
                'points': np.array(list(building['geometry'].coords)),
                'style': building['style'],
                'movable': building['movable'],
                'quality': building['quality']
            }
            out_data['buildings'].append(building_data)

    # endregion

    # region 其他
    @staticmethod
    def quick_buildings():
        points = xywh2points(44, 63, 42, 35)
        uid = Building.add_building_by_coords(points,
                                              movable=BuildingMovableType.DEMOLISHABLE,
                                              quality=BuildingQuality.GOOD,
                                              style=BuildingStyle.NORMAL,
                                              enabled=True
                                              )

        return [uid]
    # endregion


if __name__ == "__main__":
    from geo import Road
    import matplotlib.pyplot as plt

    roads = Road.quick_roads()
    _ = Building.quick_buildings()
    Object.plot_all()

    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()
    plt.show()
