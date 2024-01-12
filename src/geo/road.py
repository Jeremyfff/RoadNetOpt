import math

import numpy as np
import matplotlib.pyplot as plt
import time

import pandas as pd
from numba import jit
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import split
import networkx as nx
from geo import Object
from utils import RoadLevel, RoadState, point_utils, polyline_utils, road_utils
import style_module
import osmnx as ox
import geopandas as gpd
from collections import defaultdict
import uuid
import logging
from typing import Union
from tqdm import tqdm
from utils.common_utils import timer, duplicate_filter, rgb_to_id, id_to_rgb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class Road(Object):
    """部分功能还没有经过实验"""
    __node_attrs = ['uid', 'x', 'y', 'geometry', 'cache']
    __edge_attrs = ['u', 'v', 'uid', 'geometry', 'level', 'state', 'cache']

    __node_gdf = gpd.GeoDataFrame(columns=__node_attrs)
    __node_gdf.set_index('uid')

    __edge_gdf = gpd.GeoDataFrame(columns=__edge_attrs)
    __edge_gdf.set_index('uid')

    __coord_to_node_uid = {}  # 使用hashset代替dataframe加速_node_uid_from_coord函数

    __cached_graph = None
    __cached_node_gdf = None
    __cached_edge_gdf = None

    _flag_cached_graph_need_update = False
    __uid = uuid.uuid4()

    # region 节点相关
    @staticmethod
    def _add_node(uid, x, y, geometry):
        """
        创建单个node并添加到Road.__node_gdf中
        通过该方法添加的node，会同步更新Road.__coord_to_node_uid
        请勿自行对Road.__node_gdf进行增删或修改
        """
        new_row = {'geometry': [geometry],
                   'x': [x],
                   'y': [y],
                   'uid': [uid]
                   }
        new_gdf = gpd.GeoDataFrame(new_row, index=new_row['uid'])
        if not Road.__node_gdf.empty:
            Road.__node_gdf = gpd.pd.concat([Road.__node_gdf, new_gdf], ignore_index=False)
        else:
            Road.__node_gdf = new_gdf
        Road.__coord_to_node_uid[(x, y)] = uid
        Road.__uid = uuid.uuid4()

    @staticmethod
    def _add_nodes(uid_list, x_list, y_list, geometry_list):
        """
        一次性添加多个node到 Road.__node_gdf中
        该方法避免了多次创建df的过程，速度更快，因此在添加多个目标时应该首选该方法
        通过该方法添加的node 会同步更新Road.__coord_to_node_uid
        """
        new_row = {'geometry': geometry_list,
                   'x': x_list,
                   'y': y_list,
                   'uid': uid_list
                   }
        new_gdf = gpd.GeoDataFrame(new_row, index=new_row['uid'])
        if not Road.__node_gdf.empty:
            Road.__node_gdf = gpd.pd.concat([Road.__node_gdf, new_gdf], ignore_index=False)
        else:
            Road.__node_gdf = new_gdf
        # update
        for i in range(len(uid_list)):
            Road.__coord_to_node_uid[(x_list[i], y_list[i])] = uid_list[i]
        Road.__uid = uuid.uuid4()

    @staticmethod
    def _get_coord_uid(coord: tuple) -> uuid.UUID:
        """
        返回所处coord坐标的node的uid信息。
        如果提供的coord坐标处存在现有的node，则直接返回该node的uid；
        否则将会自动在该坐标处创建一个新的node并返回新的node的uid。
        （该方法采用hashset查找代替在dataframe中进行查找从而大幅加速，但请注意：
        该方法依赖Road.__coord_to_node_uid这个dict的加速，
        因此对于node的任何更新，必须同步到Road.__coord_to_node_uid中，
        否则将引起错误）
        """
        assert isinstance(coord, tuple)
        if coord in Road.__coord_to_node_uid:
            return Road.__coord_to_node_uid[coord]
        else:
            # create a new node
            point = Point(coord)
            uid = uuid.uuid4()
            x = coord[0]
            y = coord[1]
            Road._add_node(uid, x, y, point)
            return uid

    @staticmethod
    def _delete_node(uid):
        """
        直接删除node ，不考虑引用关系
        """
        node = Road.__node_gdf.loc[uid]
        x = node['x']
        y = node['y']
        Road.__node_gdf.drop(uid, inplace=True)
        Road.__coord_to_node_uid.pop((x, y))  # 同时删除coord_to_node_uid中缓存的坐标
        Road.__uid = uuid.uuid4()

    @staticmethod
    def _clear_node(uid):
        """
        如果没有任何road引用node， 才会将其删除
        """
        if not Road._any_road_using_node(uid):
            Road._delete_node(uid)

    @staticmethod
    def get_all_nodes():
        return Road.__node_gdf

    @staticmethod
    def _get_nodes_by_roads(roads):
        """返回被roads引用的所有node"""
        nodes = Road.__node_gdf[Road.__node_gdf['uid'].isin(roads['u']) | Road.__node_gdf['uid'].isin(roads['v'])]
        return nodes

    @staticmethod
    def _any_road_using_node(uid) -> bool:
        """判断是否有其他任何道路正在使用该node"""
        return any(Road.__edge_gdf['u'].eq(uid)) or any(Road.__edge_gdf['v'].eq(uid))

    # endregion

    # region 创建删除
    @staticmethod
    def _create_road_by_coords(coords: np.ndarray,
                               level: RoadLevel,
                               state: RoadState):
        """从坐标创建road，但不添加到__Road.__edge_gdf中"""
        geometry = point_utils.points_to_geo(coords)
        return Road._create_road_by_geometry(geometry, level, state)

    @staticmethod
    def _create_road_by_geometry(geometry: Union[LineString, Point],
                                 level: RoadLevel,
                                 state: RoadState):
        """从geometry创建road， 但不添加到__Road.__edge_gdf中"""
        # 注意，虽然创建的road没有加到Road的edge gdf中，但这里的节点将直接加到Road的node gdf中
        u = Road._get_coord_uid(geometry.coords[0])
        v = Road._get_coord_uid(geometry.coords[-1])
        uid = uuid.uuid4()
        new_row = {'u': [u],
                   'v': [v],
                   'geometry': [geometry],
                   'level': [level],
                   'state': [state],
                   'uid': [uid],
                   'cache': False
                   }
        return gpd.GeoDataFrame(new_row, index=new_row['uid'])

    @staticmethod
    def create_roads_by_coords(points_list: list[np.ndarray],
                               levels_list: list[RoadLevel],
                               states_list: list[RoadState]):
        geometry_list = [point_utils.points_to_geo(points) for points in points_list]
        return Road.create_roads_by_geometries(geometry_list, levels_list, states_list)

    @staticmethod
    def create_roads_by_geometries(geometry_list: list[LineString, Point],
                                   levels_list: list[RoadLevel],
                                   states_list: list[RoadState]):
        assert len(geometry_list) == len(levels_list) == len(states_list)
        u_list = [Road._get_coord_uid(geom.coords[0]) for geom in geometry_list]
        v_list = [Road._get_coord_uid(geom.coords[-1]) for geom in geometry_list]
        uid_list = [uuid.uuid4() for _ in geometry_list]
        new_data = {'u': u_list,
                    'v': v_list,
                    'geometry': geometry_list,
                    'level': levels_list,
                    'state': states_list,
                    'uid': uid_list
                    }
        return gpd.GeoDataFrame(new_data, index=new_data['uid'])

    @staticmethod
    def add_road(road):
        """添加road至Road.__edge_gdf"""
        if not Road.__edge_gdf.empty:
            Road.__edge_gdf = gpd.pd.concat([Road.__edge_gdf, road], ignore_index=False)
        else:
            Road.__edge_gdf = road
        Road.__uid = uuid.uuid4()
        return road['uid']

    @staticmethod
    def add_roads(roads):
        """添加roads至Road.__edge_gdf"""
        if not Road.__edge_gdf.empty:
            Road.__edge_gdf = gpd.pd.concat([Road.__edge_gdf, roads], ignore_index=False)
        else:
            Road.__edge_gdf = roads
        Road.__uid = uuid.uuid4()
        return list(roads['uid'])

    @staticmethod
    def add_road_by_coords(coords: np.ndarray,
                           level: RoadLevel,
                           state: RoadState):
        """通过坐标创建road并添加至Road.__edge_gdf"""
        road = Road._create_road_by_coords(coords, level, state)
        return Road.add_road(road)

    @staticmethod
    def _add_road_by_geometry(geometry: Union[LineString, Point],
                              level: RoadLevel,
                              state: RoadState) -> uuid.UUID:
        """通过geometry创建road并添加至Road.__edge_gdf"""
        road = Road._create_road_by_geometry(geometry, level, state)
        return Road.add_road(road)

    @staticmethod
    def add_roads_by_coords(points_list: list[np.ndarray],
                            levels_list: list[RoadLevel],
                            states_list: list[RoadState]) -> list[uuid.UUID]:
        """通过坐标创建roads并添加至Road.__edge_gdf"""
        roads = Road.create_roads_by_coords(points_list, levels_list, states_list)
        return Road.add_roads(roads)

    @staticmethod
    def _add_roads_by_geometries(geometry_list: list[LineString, Point],
                                 levels_list: list[RoadLevel],
                                 states_list: list[RoadState]) -> list[uuid.UUID]:
        """通过geometries创建road并添加至Road.__edge_gdf"""
        roads = Road.create_roads_by_geometries(geometry_list, levels_list, states_list)
        return Road.add_roads(roads)

    @staticmethod
    def delete_road(road, update_nodes_immediately=True):
        """
        删除road，默认自动清理node
        :param road: 要被删除的road
        :param update_nodes_immediately: 如果需要一次性大量删除road时，则可以不立即排查node是否要被删除。可以在所有road都被删除后统一安排清理
        :return:
        """
        uid = road['uid']
        u = road['u']
        v = road['v']

        Road.__edge_gdf.drop(uid, inplace=True)
        Road.__uid = uuid.uuid4()

        # handle cache
        if road['cache']:
            # 如果road是cached过的， 那么任何更改都会导致cache失效
            Road._flag_cached_graph_need_update = True

            # delete unused nodes
        if update_nodes_immediately:
            Road._clear_node(u)
            Road._clear_node(v)

    @staticmethod
    def delete_road_by_uid(uid, update_nodes_immediately=True):
        """通过uid删除road， 其他信息参考Road.delete_road方法"""
        Road.delete_road(Road.get_road_by_uid(uid), update_nodes_immediately)

    @staticmethod
    def delete_all(clear_cache=True):
        """清空所有内容， 默认cache也将被清除"""
        Road.__edge_gdf.drop(Road.__edge_gdf['uid'], inplace=True)
        Road.__node_gdf.drop(Road.__node_gdf['uid'], inplace=True)
        Road.__coord_to_node_uid = {}
        if clear_cache:
            Road.clear_cache()
        Road.__uid = uuid.uuid4()

    # endregion

    # region 获取查找
    @staticmethod
    def get_edge_attrs():
        return Road.__edge_attrs
    @staticmethod
    def get_node_attrs():
        return Road.__node_attrs

    @staticmethod
    def get_road_by_uid(uid: uuid.UUID):
        road = Road.__edge_gdf.loc[uid]
        return road

    @staticmethod
    def get_road_by_index(idx: int):
        road = Road.__edge_gdf.iloc[idx]
        return road

    @staticmethod
    def get_roads_by_attr_and_value(attr: str, value: any):
        assert attr in Road.__edge_attrs, f'unexpected attr ({attr}), attr must be one of these: {Road.__edge_attrs}'
        roads = Road.__edge_gdf.loc[Road.__edge_gdf[attr] == value]
        return roads

    @staticmethod
    def get_node_by_attr_and_value(attr: str, value: any):
        assert attr in Road.__node_attrs, f'unexpected attr ({attr}), attr must be one of these: {Road.__node_attrs}'
        nodes = Road.__node_gdf.loc[Road.__node_gdf[attr] == value]
        return nodes

    @staticmethod
    def get_first_road():
        return Road.get_road_by_index(0)

    @staticmethod
    def get_last_road():
        return Road.get_road_by_index(-1)

    @staticmethod
    def get_all_roads():
        return Road.__edge_gdf

    @staticmethod
    def get_roads_by_node(node):
        node_uid = node['uid']
        roads1 = Road.get_roads_by_attr_and_value('u', node_uid)
        roads2 = Road.get_roads_by_attr_and_value('v', node_uid)
        return pd.concat([roads1, roads2])

    # endregion

    # region 编辑修改
    @staticmethod
    def add_point_to_road(road, point: np.ndarray, update_nodes_immediately=True):
        if len(point.shape) == 1:
            point = np.unsqueeze(point, axis=0)
        Road.add_points_to_road(road, point, update_nodes_immediately)

    @staticmethod
    def add_points_to_road(road, points: np.ndarray, update_nodes_immediately=True):
        assert len(points.shape) == 2
        org_geo = road['geometry']
        org_points = np.array(list(org_geo.coords))
        new_points = np.vstack([org_points, points])
        Road.update_road_points(road, new_points, update_nodes_immediately)

    @staticmethod
    def update_road_points(road, points: np.ndarray, update_nodes_immediately=True):
        assert len(points.shape) == 2
        assert points.shape[0] >= 2
        uid = road['uid']
        org_geo = road['geometry']
        org_u = Road._get_coord_uid(org_geo.coords[0])
        org_v = Road._get_coord_uid(org_geo.coords[-1])

        new_points = points
        new_geo = LineString(new_points)
        new_u = Road._get_coord_uid(new_geo.coords[0])
        new_v = Road._get_coord_uid(new_geo.coords[-1])

        Road.__edge_gdf.at[uid, 'geometry'] = new_geo
        Road.__edge_gdf.at[uid, 'u'] = new_u
        Road.__edge_gdf.at[uid, 'v'] = new_v
        # handle org nodes
        if update_nodes_immediately:
            Road._clear_node(org_u)
            Road._clear_node(org_v)
        # handle cache
        if road['cache']:
            Road._flag_cached_graph_need_update = True

    @staticmethod
    def split_road(road, distance: float, normalized: bool, update_nodes_immediately=True):
        geo = road['geometry']
        uid = road['uid']
        level = road['level']
        state = road['state']

        if not isinstance(geo, LineString):
            logging.warning(f"Road geometry does not contain any LineString. "
                            f"This road ({uid}) will be skipped")
            return

        cut_point = geo.interpolate(distance, normalized)
        new_geos = list(split(geo, cut_point).geoms)
        if len(new_geos) == 1:
            return np.array(list(cut_point.coords))
        assert len(new_geos) == 2
        Road._add_road_by_geometry(new_geos[0], level=level, state=state)
        Road._add_road_by_geometry(new_geos[1], level=level, state=state)
        Road.delete_road(road, update_nodes_immediately)  # org nodes will be handled here
        # handle cache
        if road['cache']:
            Road._flag_cached_graph_need_update = True
        return np.array(list(cut_point.coords))

    @staticmethod
    def merge_roads(road1, road2, debug=True, update_nodes_immediately=True):
        if road1['level'] != road2['level']:
            if debug:
                logging.warning('不同level的道路无法合并')
            return
        if road1['state'] != road2['state']:
            if debug:
                logging.warning('不同state的道路无法合并')
            return
        if isinstance(road1['geometry'], Point) or isinstance(road2['geometry'], Point):
            if debug:
                logging.warning('geometry为point的道路暂不支持合并')
            return
        node_uids = {road1['u'], road1['v'], road2['u'], road2['v']}

        if len(node_uids) >= 4:
            if debug:
                logging.warning('道路不相邻， 无法合并')
            return
        geo1 = road1['geometry']
        geo2 = road2['geometry']
        common_point = geo1.intersection(geo2)
        if not isinstance(common_point, Point):
            if debug:
                logging.error('未知错误导致找不到common point， 跳过')
            return
        coords1 = list(geo1.coords)
        coords2 = list(geo2.coords)

        if common_point.coords[0] == geo1.coords[0]:
            coords1.reverse()
        if common_point.coords[0] == geo2.coords[-1]:
            coords2.reverse()
        new_coords = coords1[:-1] + coords2

        new_geo = LineString(new_coords)
        Road._add_road_by_geometry(new_geo, road1['level'], road1['state'])
        Road.delete_road(road1, update_nodes_immediately=update_nodes_immediately)
        Road.delete_road(road2, update_nodes_immediately=update_nodes_immediately)

    @staticmethod
    @timer
    def simplify_roads():
        org_nodes = [node for uid, node in Road.__node_gdf.iterrows()]
        org_node_count = len(org_nodes)
        print(f'原始节点数: {org_node_count}')
        for node in org_nodes:
            roads = Road.get_roads_by_node(node)
            if len(roads) == 2:
                Road.merge_roads(roads.iloc[0], roads.iloc[1])
        after_node_count = len(Road.__node_gdf)
        print(f'优化后节点数: {after_node_count}')
        print(f'{org_node_count - after_node_count}节点被优化')

    # endregion

    # region 绘图相关
    @staticmethod
    def plot_roads(roads, *args, **kwargs):
        roads = gpd.GeoDataFrame(roads, geometry='geometry')
        roads.plot(*args, **kwargs)

    @staticmethod
    def plot_all(*args, **kwargs):
        """使用geo pandas进行加速绘制"""
        Road.__edge_gdf.plot(*args, **kwargs)


    @staticmethod
    def plot_using_idx(roads, *args,**kwargs):
        line_width = [5] * len(Road.__edge_gdf)
        colors = [id_to_rgb(i) for i in range(len(Road.__edge_gdf))]

        roads_copy = roads.copy()
        roads_copy['colors'] = colors
        roads_copy['line_width'] = line_width
        roads_copy.plot(color=roads_copy['colors'],
                        linewidth=roads_copy['line_width'],
                        *args, **kwargs)

    @staticmethod
    def plot_using_style_factory(roads, style_factory, *args,**kwargs):

        colors, line_width = style_factory(roads)
        roads_copy = roads.copy()
        roads_copy['colors'] = colors
        roads_copy['line_width'] = line_width
        roads_copy.plot(color=roads_copy['colors'],
                        linewidth=roads_copy['line_width'],
                        *args, **kwargs)

    # endregion

    # region 类型转换
    @staticmethod
    def to_graph(edge_df=None, node_df=None, use_cache=True):
        """
        fast implement, version 3
        此版特性包括：
        将计算内容转移到道路的创建与修改过程中，道路将维护u和v的变量，因此创建graph时无需重新计算，大大加速了graph的创建速度
        引入缓存机制，缓存过的graph部分将不再重新创建
        """
        start_time = time.time()
        # Give initial value when value is None
        if edge_df is None:
            edge_df = Road.__edge_gdf
        if node_df is None:
            node_df = Road.__node_gdf
        if Road.__cached_graph is None and use_cache:
            use_cache = False
        # handle cache
        if use_cache:
            if Road._flag_cached_graph_need_update:
                logging.warning("You have operated on objects in the cache in previous operations without updating "
                                "the cache. This is not allowed and may cause errors.")
            G = Road.__cached_graph  # use cached graph
            edge_df = edge_df[edge_df['cache'] == False]  # filter non-cached edges
            node_df = node_df[node_df['cache'] == False]  # filter non-cached nodes
        else:
            G = nx.Graph()

        # add nodes first
        for index, row in node_df.iterrows():
            uid = row['uid']
            x = row['x']
            y = row['y']
            geometry = row['geometry']
            G.add_node(uid,
                       x=x,
                       y=y,
                       geometry=geometry)
        # add edges
        for index, row in edge_df.iterrows():
            u = row['u']
            v = row['v']
            uid = row['uid']
            geometry = row['geometry']
            state = row['state']
            level = row['level']
            G.add_edge(u, v,
                       uid=uid,
                       geometry=geometry,
                       level=level,
                       state=state)
        end_time = time.time()
        print(f"roads_to_graph 转换耗时 {(end_time - start_time) * 1000} ms")
        return G

    @staticmethod
    @duplicate_filter(logger)
    def from_graph(G):
        """
        仅使用原有的edges数据进行创建，
        highway数据将自动转化为对应的level，geometry数据将会保留
        u，v信息将被抛弃，节点信息由geometry自动计算得到
        该方法速度较慢
        """
        Road.delete_all()
        level_list = []
        state_list = []
        geometry_list = []
        for u, v, data in G.edges.data():
            if 'geometry' not in data:
                logging.info('no geometry in data')
                continue
            if 'level' in data:
                level = data['level']
            elif 'highway' in data:
                level = road_utils.highway_to_level(highway=data['highway'])
            else:
                level = RoadLevel.CUSTOM
            level_list.append(level)
            if 'state' in data:
                state = data['state']
            else:
                state = RoadState.RAW
            state_list.append(state)
            geometry_list.append(data['geometry'])
        Road._add_roads_by_geometries(geometry_list, level_list, state_list)

    @staticmethod
    @timer
    def data_to_roads(data: dict):
        assert 'roads' in data, 'invalid data'
        Road.delete_all()
        roads_data = data['roads']
        assert isinstance(roads_data, list)
        print(f"共有{len(roads_data)}条道路数据")
        points_list = []
        level_list = []
        state_list = []
        for i in tqdm(range(len(roads_data))):
            road_data = roads_data[i]
            points_list.append(np.array(road_data['points']))
            level_list.append(road_data['level'])
            state_list.append(road_data['state'])

        uid_list = Road.add_roads_by_coords(points_list, level_list, state_list)

        return uid_list

    @staticmethod
    def roads_to_data(out_data: dict):
        if 'roads' not in out_data:
            out_data['roads'] = []
        for uid, road in Road.get_all_roads().iterrows():
            road_data = {
                'points': np.array(list(road['geometry'].coords)),
                'level': road['level'],
                'state': road['state']
            }
            out_data['roads'].append(road_data)

    # endregion

    # region 其他工具
    @staticmethod
    def quick_roads():
        points = np.array([
            [0, 0],
            [0, 100],
            [-20, 20],
            [120, 20],
            [0, 20]
        ])
        uid1 = Road.add_road_by_coords(np.array([points[0], points[4]]), RoadLevel.MAIN, RoadState.RAW)
        uid2 = Road.add_road_by_coords(np.array([points[4], points[1]]), RoadLevel.MAIN, RoadState.RAW)
        uid3 = Road.add_road_by_coords(np.array([points[2], points[4]]), RoadLevel.SECONDARY, RoadState.RAW)
        uid4 = Road.add_road_by_coords(np.array([points[4], points[3]]), RoadLevel.SECONDARY, RoadState.RAW)
        return [uid1, uid2, uid3, uid4]

    @staticmethod
    def show_info():
        print(f"==================================================")
        print(f"道路数量: {len(Road.__edge_gdf)}")
        print(f"节点数量: {len(Road.__node_gdf)}")
        print(f"coord_to_uid字典长度 {len(list(Road.__coord_to_node_uid.keys()))}")
        print(f"cached graph: {Road.__cached_graph is not None}")
        print(f"cached edge gdf: {Road.__cached_edge_gdf is not None}")
        print(f"cached node gdf: {Road.__cached_node_gdf is not None}")
        print(f"==================================================")

    @staticmethod
    def cache(roads=None):
        if roads is None:
            roads = Road.__edge_gdf
            nodes = Road.__node_gdf
        else:
            nodes = Road._get_nodes_by_roads(roads)
        Road.clear_cache()

        Road.__cached_graph = Road.to_graph(edge_df=roads, node_df=nodes, use_cache=False)
        Road.__cached_node_gdf = Road.__node_gdf.copy()  # shallow copy
        Road.__cached_edge_gdf = Road.__edge_gdf.copy()  # shallow copy

        Road._flag_cached_graph_need_update = False  # update dirty variable
        for index, row in roads.iterrows():
            roads.at[index, 'cache'] = True
        for index, row in nodes.iterrows():
            nodes.at[index, 'cache'] = True

    @staticmethod
    def clear_cache():
        Road.__edge_gdf['cache'] = False
        Road.__node_gdf['cache'] = False

        Road.__cached_graph = None
        Road.__cached_edge_gdf = None
        Road.__cached_node_gdf = None

    @staticmethod
    def restore():
        if Road.__cached_edge_gdf is not None and Road.__cached_node_gdf is not None:
            Road.__edge_gdf = Road.__cached_edge_gdf
            Road.__node_gdf = Road.__cached_node_gdf
            Road._flag_cached_graph_need_update = False
            Road.rebuild_coord_to_uid_dict()  # 这里这么做是因为偷懒没有在cache的时候保存coord_to_uid的dict的副本， 因此当node gdf改变时需要更新一下
        else:
            logging.warning("no cache to restore")

    @staticmethod
    def rebuild_coord_to_uid_dict():
        """重建Road.__coord_to_node_uid"""
        Road.__coord_to_node_uid = {(row['x'], row['y']): uid for uid, row in Road.__node_gdf.iterrows()}

    # endregion


def example_roads_to_graph():
    existed_roads = Road.quick_roads()
    G = Road.to_graph()

    pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
    edge_width = {}
    # 遍历图中的每条边，根据 RoadLevel 属性来设置边的粗细
    for u, v, data in G.edges(data=True):
        road_level = data['level']
        if road_level == RoadLevel.MAIN:
            edge_width[(u, v)] = 5
        elif road_level == RoadLevel.SECONDARY:
            edge_width[(u, v)] = 3
        else:
            edge_width[(u, v)] = 1

    # 绘制图
    nx.draw(G, pos, with_labels=False, node_color='lightblue', node_size=100,
            edge_color='gray', width=[edge_width[e] for e in G.edges()])

    # 显示图
    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()
    plt.show()


def example_graph_to_roads():
    G = ox.graph_from_bbox(37.79, 37.78, -122.41, -122.43, network_type='drive')
    Road.from_graph(G)
    Road.plot_all()

    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # example_graph_to_roads()
    for i in range(10000):
        # 最大可编码16,777,216个数
        b = (i % 256)
        g = ((i // 256) % 256)
        r = ((i // 256 // 256) % 256)
        print(f'i = {i}, r = {r}, g = {g}, b = {b}')
