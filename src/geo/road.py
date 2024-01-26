import ctypes
import random
import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd
from shapely import Polygon, delaunay_triangles
from shapely.geometry import LineString, Point
from shapely.ops import split, triangulate
import networkx as nx
from geo import Object
from utils import RoadLevel, RoadState, point_utils, road_utils, RoadCluster
import geopandas as gpd
import uuid
import logging
from typing import Union, Optional
from tqdm import tqdm
from utils.common_utils import timer, duplicate_filter, id_to_rgb, to_triangles
from lib.accelerator import cAccelerator
from gui import global_var as g
from sklearn.cluster import DBSCAN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class Road(Object):
    """部分功能还没有经过实验"""
    __node_attrs = ['uid', 'geometry', 'coord', 'cache']
    #  UUID.uuid4 | shapely.Geometry | tuple | bool
    __edge_attrs = ['u', 'v', 'uid', 'geometry', 'coords', 'level', 'state', 'cache', 'geohash']
    # UUID.uuid4 | UUID.uuid4 | UUID.uuid4 | shapely.Geometry | np.ndarray | RoadLevel | RoadState | bool | int
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

    @staticmethod
    def uid():
        return Road.__uid

    # region 节点相关
    @staticmethod
    def _add_node(uid, coord: tuple):
        """
        创建单个node并添加到Road.__node_gdf中
        该方法不会检测是否存在重复坐标，请结合__coord_to_node_uid判断后添加
        请勿自行对Road.__node_gdf进行增删或修改
        """

        new_row = {'geometry': [Point(coord)],
                   'coord': [coord],
                   'uid': [uid],
                   'cache': [False]
                   }
        new_gdf = gpd.GeoDataFrame(new_row, index=new_row['uid'])
        if not Road.__node_gdf.empty:
            Road.__node_gdf = gpd.pd.concat([Road.__node_gdf, new_gdf], ignore_index=False)
        else:
            Road.__node_gdf = new_gdf
        Road.__coord_to_node_uid[coord] = uid
        Road.__uid = uuid.uuid4()

    @staticmethod
    def _add_nodes(uid_list, coords_list: list[tuple]):
        """
        一次性添加多个node到 Road.__node_gdf中
        该方法避免了多次创建df的过程，速度更快，因此在添加多个目标时应该首选该方法
        通过该方法添加的node 会同步更新Road.__coord_to_node_uid
        """
        geometry_list = [Point(coord) for coord in coords_list]
        cache_list = [False for _ in coords_list]
        new_row = {'geometry': geometry_list,
                   'coord': coords_list,
                   'cache': cache_list,
                   'uid': uid_list
                   }
        new_gdf = gpd.GeoDataFrame(new_row, index=new_row['uid'])
        if not Road.__node_gdf.empty:
            Road.__node_gdf = gpd.pd.concat([Road.__node_gdf, new_gdf], ignore_index=False)
        else:
            Road.__node_gdf = new_gdf
        # update
        for i in range(len(uid_list)):
            Road.__coord_to_node_uid[coords_list[i]] = uid_list[i]
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

        if not isinstance(coord, tuple):
            coord = tuple(coord)
        assert len(coord) == 2
        if coord in Road.__coord_to_node_uid:
            return Road.__coord_to_node_uid[coord]
        else:
            # create a new node
            uid = uuid.uuid4()
            Road._add_node(uid, coord)
            return uid

    @staticmethod
    def _delete_node(uid):
        """
        直接删除node ，不考虑引用关系
        """
        node = Road.__node_gdf.loc[uid]
        coord = node['coord']
        Road.__node_gdf.drop(uid, inplace=True)
        Road.__coord_to_node_uid.pop(coord)  # 同时删除coord_to_node_uid中缓存的坐标
        Road.__uid = uuid.uuid4()

    @staticmethod
    def _clear_node(uid):
        """
        如果没有任何road引用node， 才会将其删除
        """
        if not Road._any_road_using_node(uid):
            Road._delete_node(uid)

    @staticmethod
    def _clear_unused_nodes():
        """清除所有没有被使用的node"""
        valid_nodes = Road._get_nodes_by_roads(Road.get_all_roads())
        Road.__node_gdf = valid_nodes
        Road.rebuild_coord_to_uid_dict()

    @staticmethod
    def rebuild_coord_to_uid_dict():
        """重建Road.__coord_to_node_uid"""
        Road.__coord_to_node_uid = {row['coord']: uid for uid, row in Road.__node_gdf.iterrows()}

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
    @staticmethod
    def get_close_nodes():
        print('a')
        print(Road.__node_gdf['coord'].apply(np.array).values)
        vertex_coords = np.vstack(Road.__node_gdf['coord'].apply(np.array).values).astype(np.float32)
        print(vertex_coords.shape)

        dbscan = DBSCAN(eps=0.1, min_samples=2)  # eps 是领域的大小，min_samples 是领域内最小样本数
        labels = dbscan.fit_predict(vertex_coords)
        # 将点按簇进行分组
        groups = {}
        for i, label in enumerate(labels):
            if label not in groups:
                groups[label] = [i]
            else:
                groups[label].append(i)
        print(groups)
        return groups

    # endregion

    # region 创建删除
    @staticmethod
    def _create_road_by_coords(coords: np.ndarray,
                               level: RoadLevel,
                               state: RoadState) -> pd.Series:
        """
        从坐标创建road。
        仅创建，不添加到Road.__edge_gdf中。
        注意，虽然创建的road没有加到Road的edge gdf中，但这里的节点将直接加到Road的node gdf中
        """
        assert len(coords.shape) == 2, '提供的coords数组维度必须为2，例如(n, 2)， 其中n表示点的个数'
        geometry = point_utils.points_to_geo(coords)
        u = Road._get_coord_uid(geometry.coords[0])
        v = Road._get_coord_uid(geometry.coords[-1])
        uid = uuid.uuid4()
        new_row = {'u': [u],
                   'v': [v],
                   'geometry': [geometry],
                   'coords': [coords],
                   'level': [level],
                   'state': [state],
                   'uid': [uid],
                   'cache': False,
                   'geohash': hash(coords.tobytes())
                   }
        return gpd.GeoDataFrame(new_row, index=new_row['uid']).iloc[0]

    @staticmethod
    def create_roads_by_coords(coords_list: list[np.ndarray],
                               levels_list: list[RoadLevel],
                               states_list: list[RoadState]) -> gpd.GeoDataFrame:
        assert len(coords_list) == len(levels_list) == len(states_list)
        geometry_list = [point_utils.points_to_geo(coords) for coords in coords_list]
        u_list = [Road._get_coord_uid(coords[0]) for coords in coords_list]
        v_list = [Road._get_coord_uid(coords[-1]) for coords in coords_list]
        uid_list = [uuid.uuid4() for _ in coords_list]
        cache_list = [False for _ in coords_list]
        geohash_list = [hash(coords.tobytes()) for coords in coords_list]
        new_data = {'u': u_list,
                    'v': v_list,
                    'geometry': geometry_list,
                    'coords': coords_list,
                    'level': levels_list,
                    'state': states_list,
                    'uid': uid_list,
                    'cache': cache_list,
                    'geohash': geohash_list
                    }
        return gpd.GeoDataFrame(new_data, index=new_data['uid'])

    @staticmethod
    def add_road(road: pd.Series, return_uid: bool = True) -> Optional[uuid.UUID]:
        """添加road至Road.__edge_gdf"""
        assert isinstance(road, pd.Series)
        road_df = road.to_frame().T
        if not Road.__edge_gdf.empty:
            Road.__edge_gdf = gpd.pd.concat([Road.__edge_gdf, road_df], ignore_index=False)
        else:
            Road.__edge_gdf = road_df
        Road.__uid = uuid.uuid4()
        if return_uid:
            return road['uid']

    @staticmethod
    def add_roads(roads: gpd.GeoDataFrame, return_uid: bool = False) -> Optional[list[uuid.UUID]]:
        """添加roads至Road.__edge_gdf"""
        assert isinstance(roads, gpd.GeoDataFrame)
        if not Road.__edge_gdf.empty:
            Road.__edge_gdf = gpd.pd.concat([Road.__edge_gdf, roads], ignore_index=False)
        else:
            Road.__edge_gdf = roads
        Road.__uid = uuid.uuid4()
        if return_uid:
            return list(roads['uid'])

    @staticmethod
    def add_road_by_coords(coords: np.ndarray,
                           level: RoadLevel,
                           state: RoadState,
                           return_uid=True) -> Optional[uuid.UUID]:
        """通过坐标创建road并添加至Road.__edge_gdf"""
        road = Road._create_road_by_coords(coords, level, state)
        return Road.add_road(road, return_uid)

    @staticmethod
    def add_roads_by_coords(coords_list: list[np.ndarray],
                            levels_list: list[RoadLevel],
                            states_list: list[RoadState],
                            return_uid=False) -> Optional[list[uuid.UUID]]:
        """通过坐标创建roads并添加至Road.__edge_gdf"""
        roads = Road.create_roads_by_coords(coords_list, levels_list, states_list)
        return Road.add_roads(roads, return_uid)

    @staticmethod
    def delete_road(road: pd.Series, update_nodes_immediately=True):
        """
        删除road，默认自动清理node
        :param road: 要被删除的road
        :param update_nodes_immediately: 如果需要一次性大量删除road时，则可以不立即排查node是否要被删除。可以在所有road都被删除后统一安排清理
        :return:
        """
        assert isinstance(road, pd.Series)
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
        assert isinstance(uid, uuid.UUID)
        road = Road.__edge_gdf.loc[uid]
        return road

    @staticmethod
    def get_road_by_index(idx: int) -> pd.Series:
        assert isinstance(idx, int)
        road = Road.__edge_gdf.iloc[idx]
        return road

    @staticmethod
    def get_roads_by_indexes(idx_list: list[int]) -> gpd.GeoDataFrame:
        roads = Road.__edge_gdf.iloc[idx_list]
        return roads

    @staticmethod
    def get_roads_by_attr_and_value(attr: str, value: any) -> gpd.GeoDataFrame:
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

    @staticmethod
    def get_roads_by_cluster(cluster: RoadCluster):
        cluster = cluster.cluster
        uid_sets_by_attr = []
        for attr in cluster:
            gdfs = []
            if all(cluster[attr].values()):
                continue
            for key in cluster[attr]:
                if cluster[attr][key]:
                    _gdfs = Road.get_roads_by_attr_and_value(attr, key)
                    gdfs.append(_gdfs)
            if len(gdfs) == 0:
                return None
            gdf = pd.concat(gdfs, ignore_index=False)
            uid_sets_by_attr.append(set(gdf.index))
        if len(uid_sets_by_attr) == 0:
            return Road.get_all_roads()
        common_uid = list(set.intersection(*uid_sets_by_attr))
        return Road.get_all_roads().loc[common_uid]

    @staticmethod
    def get_road_by_hash(hash_code) -> pd.Series:
        roads = Road.get_roads_by_attr_and_value('geohash', hash_code)
        assert not roads.empty, '未找到road'
        assert len(roads) == 1, f'产生了hash碰撞, roads信息如下 {roads}'
        return roads.iloc[0]

    @staticmethod
    def get_roads_by_hashes(hashes) -> gpd.GeoDataFrame:
        hashes = set(hashes)  # 去重
        gdfs = []
        for h in hashes:
            roads = Road.get_roads_by_attr_and_value('geohash', h)
            if not roads.empty:
                gdfs.append(roads)
        assert len(gdfs) > 0
        return pd.concat(gdfs, ignore_index=False)

    @staticmethod
    def get_valid_spawn_range(road: pd.Series):
        """求可以生成新路的位置，如果没有，返回None"""
        line_string: LineString = road['geometry']
        dist_threshold = road_utils.distance_threshold_by_road_level[road['level']]
        if line_string.length < 2 * dist_threshold:
            return None, None
        return dist_threshold, line_string.length - dist_threshold

    @staticmethod
    def get_road_last_point(road: pd.Series) -> np.ndarray:
        geo = road['geometry']
        coord = list(geo.coords[-1])
        return np.array([coord])

    @staticmethod
    def get_road_last_element(road: pd.Series) -> Union[LineString, Point]:
        geo = road['geometry']
        coords = list(geo.coords)
        if len(coords) == 0:
            return geo
        pt1 = coords[-1]
        pt2 = coords[-2]
        return LineString([pt1, pt2])

    @staticmethod
    def cal_intersection_num(road: pd.Series, roads: gpd.GeoDataFrame) -> bool:
        buffered_road = road['geometry'].buffer(1e-3)
        intersects = roads['geometry'].intersects(buffered_road)
        return intersects.sum()

    # endregion

    # region 编辑修改
    @staticmethod
    def add_point_to_road(road: pd.Series, point: np.ndarray, update_nodes_immediately=True):
        assert isinstance(road, pd.Series)
        if len(point.shape) == 1:
            point = np.unsqueeze(point, axis=0)
        return Road.add_points_to_road(road, point, update_nodes_immediately)

    @staticmethod
    def add_points_to_road(road: pd.Series, points: np.ndarray, update_nodes_immediately=True):
        assert len(points.shape) == 2
        assert isinstance(road, pd.Series)
        org_coords = road['coords']
        new_points = np.vstack([org_coords, points])
        return Road.update_road_points(road, new_points, update_nodes_immediately)

    @staticmethod
    def update_road_points(road: pd.Series, points: np.ndarray, update_nodes_immediately=True):
        assert len(points.shape) == 2
        assert isinstance(road, pd.Series)
        assert points.shape[0] >= 2
        uid = road['uid']
        org_u = road['u']
        org_v = road['v']

        new_points = points
        new_geo = LineString(new_points)
        new_u = Road._get_coord_uid(new_geo.coords[0])
        new_v = Road._get_coord_uid(new_geo.coords[-1])

        Road.__edge_gdf.at[uid, 'coords'] = new_points
        Road.__edge_gdf.loc[uid, 'geometry'] = new_geo
        Road.__edge_gdf.loc[uid, 'u'] = new_u
        Road.__edge_gdf.loc[uid, 'v'] = new_v
        # handle org nodes
        if update_nodes_immediately:
            Road._clear_node(org_u)
            Road._clear_node(org_v)
        # handle cache
        try:
            if road['cache'].any():
                Road._flag_cached_graph_need_update = True
        except Exception as e:
            print(e)
        return Road.get_road_by_uid(uid)

    @staticmethod
    def split_road(road: pd.Series, distance: float, normalized: bool, update_nodes_immediately=True) -> Optional[
        np.ndarray]:
        assert isinstance(road, pd.Series)
        uid = road['uid']
        geo = road['geometry']
        if not isinstance(geo, LineString):
            logging.warning(f"Road geometry does not contain any LineString. "
                            f"This road ({uid}) will be skipped")
            return
        # Negative length values are taken as measured in the reverse direction from the end of the geometry.
        # Out-of-range index values are handled by clamping them to the valid range of values.
        # If the normalized arg is True, the distance will be interpreted as a fraction of the geometry's length.
        cut_point: Point = geo.interpolate(distance, normalized)
        if cut_point.is_empty:
            logging.warning(f"Cut failed. Cut_point is empty. Please check your road geometry."
                            f"This road ({uid}) will be skipped")
            return
        coord = np.array(cut_point.coords)[0]
        coord_uid, road_uids = Road.split_road_by_coord(road, coord, update_nodes_immediately)
        return np.array(Road.__node_gdf.loc[coord_uid]['coord']).reshape(1, 2)

    @staticmethod
    def split_road_by_coord(road: pd.Series, coord: np.ndarray, update_nodes_immediately=True):
        coord = coord.reshape(2)
        org_coords = road['coords']
        org_level = road['level']
        org_state = road['state']
        distances = np.linalg.norm(org_coords - coord, axis=1)
        closest_point_indices = np.argsort(distances)[:2].tolist()
        idx1 = min(closest_point_indices)
        idx2 = max(closest_point_indices)
        assert idx2 - idx1 == 1
        coord_uid = Road._get_coord_uid(coord)
        if coord_uid == road['u'] or coord_uid == road['v']:
            print(f'use existed coord')
            road_uids = [road['uid']]
        else:
            common_coord = coord.reshape(1, 2)
            coords1 = np.vstack([org_coords[:idx2, :], common_coord])
            uid1 = Road.add_road_by_coords(coords1, org_level, org_state, return_uid=True)
            coords2 = np.vstack([common_coord, org_coords[idx2:, :]])
            uid2 = Road.add_road_by_coords(coords2, org_level, org_state, return_uid=True)
            road_uids = [uid1, uid2]
            coord_uid = Road._get_coord_uid(coord)
            Road.delete_road(road, update_nodes_immediately)  # org nodes will be handled here
            # handle cache
            if road['cache']:
                Road._flag_cached_graph_need_update = True
        return coord_uid, road_uids

    @staticmethod
    def split_road_by_random_position(road: pd.Series):
        """随机选取一个位置作为新路的出生点，并且将路进行分割， 返回分割点"""
        dist_min, dist_max = Road.get_valid_spawn_range(road)
        if dist_min is None or dist_max is None:
            return None
        dist = random.uniform(dist_min, dist_max)
        return Road.split_road(road, dist, normalized=False)

    @staticmethod
    def detect_intersection_and_split(road: pd.Series, roads: gpd.GeoDataFrame):
        """road即图中a2，即在生长的路， roads即其他需要和他判断是否相交的道路"""
        # 判断交点

        # 筛选出合理的交点

        # 根据交点分割碰撞的道路，并裁剪生长的道路

        # 返回？？

    @staticmethod
    def merge_roads(road1: pd.Series, road2: pd.Series, debug=True, update_nodes_immediately=True):
        assert isinstance(road1, pd.Series)
        assert isinstance(road2, pd.Series)
        if road1['level'] != road2['level']:
            if debug:
                logging.warning('不同level的道路无法合并')
            return
        if road1['state'] != road2['state']:
            if debug:
                logging.warning('不同state的道路无法合并')
            return
        coords1 = road1['coords']
        coords2 = road2['coords']
        if len(coords1) <= 1 or len(coords2) <= 1:
            if debug:
                logging.warning('只有一个点的道路暂不支持合并')
            return
        node_uids = {road1['u'], road1['v'], road2['u'], road2['v']}
        if len(node_uids) >= 4:
            if debug:
                logging.warning('没有找到共享的node， 无法合并')
            return
        if len(node_uids) <= 2:
            if debug:
                logging.warning('道路完全重合')
            Road.delete_road(road2, update_nodes_immediately=update_nodes_immediately)
            return road1
        if road1['u'] == road2['u']:
            # (<v---coords1---u) (u---coords2---v>)
            coords1 = coords1[::-1, :]  # 翻转
        elif road1['u'] == road2['v']:
            # (<v---coords1---u) (<v---coords2---u)
            coords1 = coords1[::-1, :]  # 翻转
            coords2 = coords2[::-1, :]  # 翻转
        elif road1['v'] == road2['u']:
            # (u---coords1---v>) (u---coords2---v>)
            pass
        elif road1['v'] == road2['v']:
            # (u---coords1---v>) (<v---coords2---u)
            coords2 = coords2[::-1, :]  # 翻转
        else:
            raise Exception
        new_coords = np.vstack((coords1[:-1, :], coords2))
        Road.add_road_by_coords(new_coords, road1['level'], road1['state'])
        Road.delete_road(road1, update_nodes_immediately=update_nodes_immediately)
        Road.delete_road(road2, update_nodes_immediately=update_nodes_immediately)

    @staticmethod
    @timer
    def simplify_roads():
        org_nodes = [node for uid, node in Road.__node_gdf.iterrows()]  # 这里必须创建一份副本，否则对node 的删改会改变列表
        org_node_count = len(Road.__node_gdf)
        print(f'原始节点数: {org_node_count}')
        for node in org_nodes:
            roads = Road.get_roads_by_node(node)
            if len(roads) == 2:
                Road.merge_roads(roads.iloc[0], roads.iloc[1], update_nodes_immediately=True)
        after_node_count = len(Road.__node_gdf)
        print(f'优化后节点数: {after_node_count}')
        print(f'{org_node_count - after_node_count}节点被优化')

    # endregion

    # region 绘图相关
    @staticmethod
    def plot_nodes(nodes, *args, **kwargs):
        if nodes is None:
            return
        nodes = gpd.GeoDataFrame(nodes, geometry='geometry')
        nodes.plot(*args, **kwargs)

    @staticmethod
    def plot_roads(roads, *args, **kwargs):
        if roads is None:
            return
        roads = gpd.GeoDataFrame(roads, geometry='geometry')
        roads.plot(*args, **kwargs)

    @staticmethod
    def plot_all(*args, **kwargs):
        """使用geo pandas进行加速绘制"""
        Road.__edge_gdf.plot(*args, **kwargs)

    @staticmethod
    def plot_using_idx(roads, *args, **kwargs):
        if roads is None:
            return
        line_width = [5] * len(Road.__edge_gdf)
        colors = [id_to_rgb(i) for i in range(len(Road.__edge_gdf))]

        roads_copy = roads.copy()
        roads_copy['colors'] = colors
        roads_copy['line_width'] = line_width
        roads_copy.plot(color=roads_copy['colors'],
                        linewidth=roads_copy['line_width'],
                        *args, **kwargs)

    @staticmethod
    def plot_using_style_factory(roads, style_factory, *args, **kwargs):
        if roads is None:
            return
        colors, line_width = style_factory(roads)
        roads_copy = roads.copy()
        roads_copy['colors'] = colors
        roads_copy['line_width'] = line_width
        roads_copy.plot(color=roads_copy['colors'],
                        linewidth=roads_copy['line_width'],
                        *args, **kwargs)

    @staticmethod
    def get_vertices_data_legacy(roads, style_factory):
        params = style_factory(roads)
        colors = params[0]
        widths = params[1]

        vertex_coords = []  # 所有顶点坐标
        vertex_colors = []  # 所有顶点颜色
        i = 0
        for uid, road in roads.iterrows():
            road_poly: Polygon = road['geometry'].buffer(widths[i] * 5, quad_segs=1, cap_style='flat')
            # quad_segs: 指定圆弧近似值中四分之一圆内的线性段数。
            # shapely.BufferCapStyle 可在 {'round', 'square', 'flat'} 中选择, 默认 'round'

            delauney = to_triangles(road_poly)
            new_coords = np.array([list(triangle.exterior.coords) for triangle in delauney])[:, :3, :]
            new_coords = new_coords.reshape(-1, new_coords.shape[-1])

            vertex_coords.append(new_coords)
            vertex_colors.extend([colors[i]] * len(new_coords))
            i += 1
        vertex_coords = np.vstack(vertex_coords)
        vertex_colors = np.array(vertex_colors)
        if vertex_colors.shape[1] == 3:
            vertex_colors = np.concatenate((vertex_colors, np.ones((len(vertex_colors), 1))), axis=1)
        vertices = np.concatenate((vertex_coords, vertex_colors), axis=1).astype(np.float32)
        return vertices

    @staticmethod
    def get_vertices_data(roads, style_factory, debug=False):
        start_time = time.time()
        params = style_factory(roads)
        colors = params[0]
        widths = params[1]
        num_roads = len(roads)
        first = np.empty(num_roads, dtype=np.int32)
        num_vertices = np.empty(num_roads, dtype=np.int32)
        vertex_coords = roads['coords']
        i = 0
        total = 0
        for coords in vertex_coords:
            num = len(coords)
            first[i] = total
            num_vertices[i] = num
            total += num
            i += 1
        vertex_coords = np.concatenate(vertex_coords.values, axis=0)
        vertex_coords = np.array(vertex_coords, dtype=np.float32).tobytes()  # 4 + 4 bytes
        first = np.array(first, dtype=np.int32).tobytes()  # 4 byte
        num_vertices = np.array(num_vertices, dtype=np.int32).tobytes()  # 4 bytes
        colors = np.array(colors, dtype=np.float32)
        if colors.shape[1] == 3:
            colors = np.concatenate((colors, np.ones((len(colors), 1), dtype=np.float32)), axis=1)
        colors = colors.tobytes()  # 4 + 4 + 4 + 4  bytes
        widths = np.array(widths, dtype=np.float32) * g.LINE_WIDTH_SCALE  # width multiplier
        widths = widths.tobytes()  # 4 bytes
        if debug:
            print(f'prepare bytes 消耗时间 = {time.time() - start_time}s')
            start_time = time.time()
        buffer = cAccelerator.TriangulatePolylines(vertex_coords, first, num_vertices, colors, widths)
        if debug:
            print(f'c# 代码消耗时间 = {time.time() - start_time}s')
            start_time = time.time()
        py_bytes = bytes(buffer)
        vertices = np.frombuffer(py_bytes, np.float32).reshape(-1, 6)
        if debug:
            print(f'转换为numpy消耗时间 = {time.time() - start_time}s')
        return vertices

    @staticmethod
    def get_node_vertices_data(nodes: gpd.GeoDataFrame, style_factory):
        params = style_factory(nodes)
        colors = params[0]
        widths = params[1]
        vertex_coords = np.concatenate(nodes['coord'].apply(np.array).values, axis=0).astype(np.float32)
        print(vertex_coords.shape)
        vertex_coords = vertex_coords.tobytes()  # 4 + 4 bytes
        colors = np.array(colors, dtype=np.float32)
        if colors.shape[1] == 3:
            colors = np.concatenate((colors, np.ones((len(colors), 1), dtype=np.float32)), axis=1)
        colors = colors.tobytes()  # 4 + 4 + 4 + 4  bytes
        widths = np.array(widths, dtype=np.float32) * g.LINE_WIDTH_SCALE  # width multiplier
        widths = widths.tobytes()  # 4 bytes
        buffer = cAccelerator.TriangulatePoints(vertex_coords, colors, widths)
        py_bytes = bytes(buffer)
        vertices = np.frombuffer(py_bytes, np.float32).reshape(-1, 6)
        return vertices

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
            edge_df = edge_df[~edge_df['cache']]  # filter non-cached edges
            node_df = node_df[~node_df['cache']]  # filter non-cached nodes
        else:
            G = nx.Graph()
        # add nodes first
        for index, row in node_df.iterrows():
            uid = row['uid']
            x, y = row['coord']
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
            coords = row['coords']
            state = row['state']
            level = row['level']
            G.add_edge(u, v,
                       uid=uid,
                       geometry=geometry,
                       coords=coords,
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
        coords_list = []
        level_list = []
        state_list = []
        for u, v, data in G.edges.data():
            if 'coords' not in data:
                logging.warning('No coords in data!')
                continue

            if 'level' in data:
                level = data['level']
            elif 'highway' in data:
                level = road_utils.highway_to_level(highway=data['highway'])
            else:
                level = RoadLevel.UNDEFINED
            level_list.append(level)

            if 'state' in data:
                state = data['state']
            else:
                state = RoadState.RAW

            state_list.append(state)
            coords_list.append(data['coords'])
        Road.add_roads_by_coords(coords_list, level_list, state_list)

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
        uid1 = Road.add_road_by_coords(np.array([points[0], points[4]]), RoadLevel.TRUNK, RoadState.RAW)
        uid2 = Road.add_road_by_coords(np.array([points[4], points[1]]), RoadLevel.TRUNK, RoadState.RAW)
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
            roads.loc[index, 'cache'] = True
        for index, row in nodes.iterrows():
            nodes.loc[index, 'cache'] = True

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
        Road.__uid = uuid.uuid4()

    # endregion


if __name__ == "__main__":
    pass
