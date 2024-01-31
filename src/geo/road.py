import random
import numpy as np
import time
from collections import defaultdict
import pandas as pd
from shapely import Polygon, delaunay_triangles
from shapely.geometry import LineString, Point
import networkx as nx
from geo import Object
from utils import RoadLevel, RoadState, point_utils, road_utils, RoadCluster
import geopandas as gpd
import uuid
import logging
from typing import Union, Optional
from tqdm import tqdm
from utils.common_utils import timer, duplicate_filter, id_to_rgb, to_triangles
from lib.accelerator import cAccelerator, cRoadAccelerator, arrs_addr_len
from gui import global_var as g
from sklearn.cluster import DBSCAN
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

PRECISION = 10


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

    # region 全局
    @staticmethod
    def uid():
        return Road.__uid

    # endregion

    # region 节点相关

    @staticmethod
    def get_node_by_uid(uid):
        return Road.__node_gdf.loc[uid]
    @staticmethod
    def get_node_by_index(idx: int) -> pd.Series:
        assert isinstance(idx, int)
        node = Road.__node_gdf.iloc[idx]
        return node

    @staticmethod
    def get_nodes_by_indexes(idx_list: list[int]) -> gpd.GeoDataFrame:
        nodes = Road.__node_gdf.iloc[idx_list]
        return nodes

    @staticmethod
    def get_node_coord(uid) -> tuple:
        return Road.get_node_by_uid(uid)['coord']

    @staticmethod
    def _get_or_create_node_by_coord(coord: tuple) -> uuid.UUID:
        """
        返回所处coord坐标的node的uid信息。
        如果提供的coord坐标处存在现有的node，则直接返回该node的uid；
        否则将会自动在该坐标处创建一个新的node并返回新的node的uid。
        """
        # validation
        if not isinstance(coord, tuple):
            coord = tuple(coord)
        assert len(coord) == 2
        # 离散化
        x = round(coord[0] * PRECISION) / PRECISION
        y = round(coord[1] * PRECISION) / PRECISION
        coord = (x, y)
        # 判断是否已经存在
        if coord in Road.__coord_to_node_uid:
            return Road.__coord_to_node_uid[coord]
        else:
            # 创建新的node
            uid = uuid.uuid4()
            new_row = {'geometry': [Point(coord)], 'coord': [coord], 'uid': [uid], 'cache': [False]}
            new_gdf = gpd.GeoDataFrame(new_row, index=new_row['uid'])
            if not Road.__node_gdf.empty:
                Road.__node_gdf = gpd.pd.concat([Road.__node_gdf, new_gdf], ignore_index=False)
            else:
                Road.__node_gdf = new_gdf
            # 添加coord至__coord_to_node_uid
            Road.__coord_to_node_uid[coord] = uid
            Road.__uid = uuid.uuid4()  # 更新global uid
            return uid

    @staticmethod
    def _get_node_by_coord(coord: tuple) -> Optional[uuid.UUID]:
        """判断坐标处是否存在node，如果存在，返回node的uid， 如果不存在，返回None"""
        if not isinstance(coord, tuple):
            coord = tuple(coord)
        assert len(coord) == 2
        x = round(coord[0] * PRECISION) / PRECISION
        y = round(coord[1] * PRECISION) / PRECISION
        coord = (x, y)
        if coord in Road.__coord_to_node_uid:
            return Road.__coord_to_node_uid[coord]
        else:
            return None

    @staticmethod
    def _delete_node(uid):
        """直接删除node ，不考虑引用关系"""
        node = Road.__node_gdf.loc[uid]
        coord = node['coord']
        x = round(coord[0] * PRECISION) / PRECISION
        y = round(coord[1] * PRECISION) / PRECISION
        coord = (x, y)
        Road.__node_gdf.drop(uid, inplace=True)
        Road.__coord_to_node_uid.pop(coord)  # 同时删除coord_to_node_uid中缓存的坐标
        Road.__uid = uuid.uuid4()

    @staticmethod
    def _clear_node(uid):
        """如果没有任何road引用node， 才会将其删除"""
        if not Road._any_road_using_node(uid):
            Road._delete_node(uid)

    @staticmethod
    def clear_unused_nodes():
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
        return Road.__node_gdf[Road.__node_gdf['uid'].isin(roads['u']) | Road.__node_gdf['uid'].isin(roads['v'])]

    @staticmethod
    def _any_road_using_node(uid) -> bool:
        """判断是否有其他任何道路正在使用该node"""
        return any(Road.__edge_gdf['u'].eq(uid)) or any(Road.__edge_gdf['v'].eq(uid))

    @staticmethod
    def get_close_nodes(eps=0.1, min_samples=2) -> dict[int:gpd.GeoDataFrame]:
        """
        获取几乎重叠的nodes组
        :param eps: 领域的大小
        :param min_samples: 领域内最小样本数, 默认为2
        :return: 靠近的nodes的分组dict， key为组别， value为GeoDataFrame， 包含了这个组的所有nodes
        """
        vertex_coords = np.vstack(Road.__node_gdf['coord'].apply(np.array).values).astype(np.float32)
        # 从向量数组或距离矩阵执行 DBSCAN 聚类。
        # DBSCAN - 基于密度的噪声应用程序空间聚类。 找到高密度的核心样本并从中扩展簇。 适用于包含相似密度簇的数据。
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(vertex_coords)
        # 将点按簇进行分组
        groups = defaultdict(list)
        for i, label in enumerate(labels):
            groups[label].append(i)
        groups = dict(groups)
        groups.pop(-1)
        groups_nodes = {label: Road.__node_gdf.iloc[idx_list] for label, idx_list in groups.items()}
        return groups_nodes

    @staticmethod
    def get_nodes_avg_coord(nodes: gpd.GeoDataFrame):
        avg_coord = nodes['coord'].apply(pd.Series).mean()
        return tuple(avg_coord)

    @staticmethod
    def merge_nodes(nodes: gpd.GeoDataFrame):
        logging.debug(f'================正在执行合并nodes===============')
        logging.debug(f'正在合并 [{len(nodes)}]个 nodes, 原始nodes的信息如下')
        logging.debug('----------------------------------------------------------------------------')
        logging.debug(f'坐标为: {", ".join([str(node["coord"]) for node_uid, node in nodes.iterrows()])}')
        logging.debug(f'uid为: {", ".join([str(node_uid) for node_uid, node in nodes.iterrows()])}')
        logging.debug('----------------------------------------------------------------------------')
        avg_coord = Road.get_nodes_avg_coord(nodes)  # (tuple)
        new_node_uid = Road._get_or_create_node_by_coord(avg_coord)  # create or get new node
        new_node_coord = Road.get_node_coord(new_node_uid)  # 重新获取坐标 (tuple)
        logging.debug(f'新node的uid为: {new_node_uid}')
        logging.debug(f'新node的坐标为: {new_node_coord}')
        new_node_coord = np.array(new_node_coord)  # (2, )
        updated_roads_uid = set()
        i = 0
        for node_uid, node in nodes.iterrows():
            logging.debug(f'[node {i}] 正在分析node ({node["uid"]})')
            related_roads = Road.get_roads_by_node(node)
            logging.debug(f'[node {i}] 找到[{len(related_roads)}]条相关road')
            j = 0
            for road_uid, road in related_roads.iterrows():
                if road_uid in updated_roads_uid:
                    logging.debug(f'    [road {j}] 遇到了已经计算过的road({road_uid})， 跳过')
                    continue
                updated_roads_uid.add(road_uid)
                logging.debug(f'    [road {j}] 准备更新 road ({road_uid})')
                u_coord = Road.get_node_coord(road['u'])  # tuple
                v_coord = Road.get_node_coord(road['v'])  # tuple
                u_dist_sq = (new_node_coord[0] - u_coord[0]) ** 2 + (new_node_coord[1] - u_coord[1]) ** 2
                v_dist_sq = (new_node_coord[0] - v_coord[0]) ** 2 + (new_node_coord[1] - v_coord[1]) ** 2
                logging.debug(f'    [road {j}] 新road两端距离新node的距离平方分别为: {u_dist_sq}, {v_dist_sq}')
                if u_dist_sq < v_dist_sq:
                    logging.debug(f'    [road {j}] u端更近')
                    # road_coords[0] = new_node_coord
                    Road.replace_u(road, new_node_uid)

                else:
                    logging.debug(f'    [road {j}] v端更近')
                    # road_coords[-1] = new_node_coord
                    Road.replace_v(road, new_node_uid)

                # Road.update_road_points(road, road_coords)
                logging.debug(f'    [road {j}] 已更新road ({road["uid"]})')
                j += 1
            i += 1
        logging.debug(f'================合并完成===============')

    @staticmethod
    def merge_all_close_nodes():
        groups = Road.get_close_nodes()
        for _, nodes in groups.items():
            Road.merge_nodes(nodes)
        Road.clear_unused_nodes()

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
        coords = coords.copy()
        u = Road._get_or_create_node_by_coord(coords[0])
        v = Road._get_or_create_node_by_coord(coords[-1])
        # 重新更新首尾坐标
        coords[0] = np.array(Road.get_node_coord(u))
        coords[-1] = np.array(Road.get_node_coord(v))
        geometry = point_utils.points_to_geo(coords)
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
        u_list = [Road._get_or_create_node_by_coord(coords[0]) for coords in coords_list]
        v_list = [Road._get_or_create_node_by_coord(coords[-1]) for coords in coords_list]
        # 重新计算首尾coords
        for i, coords in enumerate(coords_list):
            coords[0] = np.array(Road.get_node_coord(u_list[i]))
            coords[-1] = np.array(Road.get_node_coord(v_list[i]))
        geometry_list = [point_utils.points_to_geo(coords) for coords in coords_list]
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
    def delete_roads_by_uids_list(uids_list: list[uuid.UUID]):
        for uid in uids_list:
            Road.delete_road_by_uid(uid)

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
        new_u = Road._get_or_create_node_by_coord(new_points[0])
        new_v = Road._get_or_create_node_by_coord(new_points[-1])
        # 重新根据u和v的node的坐标 更新 new_points
        new_points[0] = np.array(Road.get_node_coord(new_u))
        new_points[-1] = np.array(Road.get_node_coord(new_v))
        new_geo = LineString(new_points)

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
            if road['cache']:
                Road._flag_cached_graph_need_update = True
        except Exception as e:
            print(e)
        return Road.get_road_by_uid(uid)

    @staticmethod
    def replace_u(road, u_uid):
        road_uid = road['uid']
        new_coords = road['coords'].copy()
        new_coords[0] = np.array(Road.get_node_coord(u_uid))
        new_geo = LineString(new_coords)
        Road.__edge_gdf.at[road_uid, 'coords'] = new_coords
        Road.__edge_gdf.loc[road_uid, 'geometry'] = new_geo
        Road.__edge_gdf.loc[road_uid, 'u'] = u_uid

    @staticmethod
    def replace_v(road, v_uid):
        road_uid = road['uid']
        new_coords = road['coords'].copy()
        new_coords[-1] = np.array(Road.get_node_coord(v_uid))
        new_geo = LineString(new_coords)
        Road.__edge_gdf.at[road_uid, 'coords'] = new_coords
        Road.__edge_gdf.loc[road_uid, 'geometry'] = new_geo
        Road.__edge_gdf.loc[road_uid, 'v'] = v_uid

    @staticmethod
    def detect_intersection(candidate_roads: gpd.GeoDataFrame, all_roads: gpd.GeoDataFrame):
        """
        计算道路相交， all_roads必须全包含roads。该方法依赖c#实现
        :param candidate_roads: 准备计算相交的道路
        :param all_roads: 参与计算的道路域
        :return: 返回谁和谁相交在哪
                 1. 相交的道路uid：list[tuple[uuid.UUID, uuid.UUID]]
                 2. 交点：list[tuple[float, float]]
        """
        _start_time = time.time()
        in_first = np.empty(len(all_roads), dtype=np.int32)
        in_num = np.empty(len(all_roads), dtype=np.int32)
        vertex_coords = all_roads['coords']
        i = 0
        total = 0
        for coords in vertex_coords:
            num = len(coords)
            in_first[i] = total
            in_num[i] = num
            total += num
            i += 1
        vertex_coords = np.concatenate(vertex_coords.values, dtype=np.float32, axis=0)
        in_vertex_x = vertex_coords[:, 0].copy()
        in_vertex_y = vertex_coords[:, 1].copy()
        in_candidate_idx = np.array(
            [all_roads.index.get_loc(uid) for uid in candidate_roads.index], dtype=np.int32
        )
        logging.debug(f'准备数据时间 {time.time() - _start_time}s')
        _start_time = time.time()
        logging.debug(f'进入c#处理')
        """
        /// <summary>
        /// 批量计算道路相交
        /// </summary>
        /// <param name="addrVerticesX">顶点坐标x的内存地址</param>
        /// <param name="lenVerticesX">顶点坐标x的个数</param>
        /// <param name="addrVerticesY">顶点坐标y的内存地址</param>
        /// <param name="lenVerticesY">顶点坐标y的个数</param>
        /// <param name="addrFirst">记录了polyline起始点的index序号的array的内存地址</param>
        /// <param name="lenFirst">记录了polyline起始点的index序号的array的长度， 即polyline的个数</param>
        /// <param name="addrNumVerticesPerPolyline">记录了每个polyline顶点个数的array的内存地址</param>
        /// <param name="lenNumVerticesPerPolyline">记录了每个polyline顶点个数的array的长度， 即polyline的个数</param>
        /// <param name="addrIdxToCalculate">记录了哪些idx的polyline需要参与交点计算的array的内存地址</param>
        /// <param name="lenIdxToCalculate">记录了哪些idx的polyline需要参与交点计算的array的长度， 即需要计算的polyline的个数</param>
        ///  returns:
        ///   idx1    | idx2   | x      | y
        ///   int32   | int32  | float32| float32
        ///   4 bytes | 4 bytes| 4 bytes| 4 bytes
        """
        c_params = arrs_addr_len(in_vertex_x, in_vertex_y, in_first, in_num, in_candidate_idx)
        buffer = cRoadAccelerator.RoadIntersection(*c_params)
        logging.debug(f'c# 处理数据总耗时(含数据传输和解析) {time.time() - _start_time}s')

        data = np.frombuffer(bytes(buffer), dtype=np.int32).reshape(-1, 4)  # idx1, idx2, pt_x, pt_y
        idx_data = data[:, :2].astype(np.int32)
        intersection_data = data[:, 2:].view(np.float32)
        out_valid_uid_data: list[tuple[uuid.UUID, uuid.UUID]] = []
        out_valid_intersection_data: list[tuple[float, float]] = []
        # 去重，去正常相交
        calculated_idx_pair = set()
        for i in range(len(idx_data)):
            idx1 = int(idx_data[i][0])
            idx2 = int(idx_data[i][1])
            if not (idx1, idx2) in calculated_idx_pair:
                calculated_idx_pair.add((idx1, idx2))
                calculated_idx_pair.add((idx2, idx1))
            else:
                continue  # 去除已经计算过的道路
            road1, road2 = all_roads.iloc[idx1], all_roads.iloc[idx2]
            uid1, uid2 = road1['uid'], road2['uid']
            uid_set = {road1['u'], road1['v'], road2['u'], road2['v']}
            if len(uid_set) <= 3: continue  # 去除掉本身就首尾相接的道路
            out_valid_uid_data.append((uid1, uid2))
            out_valid_intersection_data.append(tuple(intersection_data[i]))
        # 完成去重
        return out_valid_uid_data, out_valid_intersection_data

    @staticmethod
    def _UidUidPoint_to_UidPoints(road_uid_data, intersection_data):
        # 转置为每条道路上的分割点
        uid_points_dict: dict[uuid.UUID:set[tuple[float, float]]] = {}  # {uuid, set(intersection points)} 记录每条道路上的分割点
        for i in range(len(road_uid_data)):
            uid1, uid2 = road_uid_data[i][0], road_uid_data[i][1]
            intersection_point = intersection_data[i]  # tuple
            if uid1 not in uid_points_dict.keys():
                uid_points_dict[uid1] = set()
            if uid2 not in uid_points_dict.keys():
                uid_points_dict[uid2] = set()
            uid_points_dict[uid1].add(intersection_point)
            uid_points_dict[uid2].add(intersection_point)
        # 至此得到了uid道路的分割点位置的dict，  key为uid, value为set[tuple(float, float)]
        return uid_points_dict

    @staticmethod
    def interpolate_road(road, distance, normalized) -> Optional[np.ndarray]:
        """在road上取点， 失败返回None"""
        uid = road['uid']
        geo = road['geometry']
        if not isinstance(geo, LineString):
            logging.warning(f"Road geometry does not contain any LineString. "
                            f"This road ({uid}) will be skipped")
            return None
        cut_point: Point = geo.interpolate(distance, normalized)
        if cut_point.is_empty:
            logging.warning(f"Cut failed. Cut_point is empty. Please check your road geometry."
                            f"This road ({uid}) will be skipped")
            return None
        coord = np.array(cut_point.coords)[0]  # shape= (2, )
        return coord

    @staticmethod
    def interpolate_road_by_random_position(road: pd.Series):
        dist_min, dist_max = Road.get_valid_spawn_range(road)
        if dist_min is None or dist_max is None:
            return None
        dist = random.uniform(dist_min, dist_max)
        return Road.interpolate_road(road, dist, normalized=False)

    @staticmethod
    def split_road(road: pd.Series, distance: float, normalized: bool) -> list[uuid.uuid4()]:
        """先取点，后分割，返回分割后的list[uid]， 失败返回自身uid"""
        assert isinstance(road, pd.Series)
        coord = Road.interpolate_road(road, distance, normalized)  # (2, )
        if coord is None: return [road['uid']]
        return Road.split_road_by_coord(road, coord)

    @staticmethod
    def split_road_by_coord(road: pd.Series, split_coord: np.ndarray) -> list[uuid.uuid4()]:
        """通过坐标点分割道路， 返回分割后的list[uid]， 失败返回自身uid"""
        split_coord = split_coord.reshape(2)
        uid = Road._get_node_by_coord(split_coord)
        if road['u'] == uid or road['v'] == uid:
            return [road['uid']]
        split_coord = split_coord.reshape(-1, 2)
        return Road.split_road_by_coords(road, split_coord)

    @staticmethod
    def split_road_by_coords(road: pd.Series, split_coords: np.ndarray) -> list[uuid.uuid4()]:
        """通过一系列坐标点分割道路，返回分割后的list[uid]， 失败返回自身uid
        该方法调用c#实现"""
        assert isinstance(split_coords, np.ndarray)
        split_coords = split_coords.reshape(-1, 2)  # (n, 2)
        road_coords = road['coords']
        road_coords_x = road_coords[:, 0].astype(np.float32).copy()
        road_coords_y = road_coords[:, 1].astype(np.float32).copy()
        split_coords_x = split_coords[:, 0].astype(np.float32).copy()
        split_coords_y = split_coords[:, 1].astype(np.float32).copy()
        # c# code
        c_params = arrs_addr_len(road_coords_x, road_coords_y, split_coords_x, split_coords_y)
        result = cRoadAccelerator.SplitRoad(*c_params)

        new_road_coords = np.frombuffer(bytes(result.Item1), dtype=np.float32).reshape(-1, 2)
        new_road_coords_num = np.frombuffer(bytes(result.Item2), dtype=np.int32)
        segmented_road_coords = np.split(new_road_coords, np.cumsum(new_road_coords_num)[:-1])
        org_level = road['level']
        org_state = road['state']
        Road.delete_road(road)
        new_uids = []
        for road_coords in segmented_road_coords:
            uid = Road.add_road_by_coords(road_coords, org_level, org_state)
            new_uids.append(uid)
        return new_uids

    @staticmethod
    def split_roads_by_intersection_data(road_uid_data: list[tuple[uuid.UUID, uuid.UUID]],
                                         intersection_data: list[tuple[float, float]]):
        uid_point_dict = Road._UidUidPoint_to_UidPoints(road_uid_data, intersection_data)
        for uid, intersection_points in uid_point_dict.items():
            logging.debug(f'正在分割road {uid}, 上面有{len(intersection_points)}个点')
            road = Road.get_road_by_uid(uid)
            intersection_points = list(intersection_points)  # list[tuple(float, float)]
            intersection_points = np.array(intersection_points).reshape(-1, 2)  # (n, 2)
            Road.split_road_by_coords(road, intersection_points)

    @staticmethod
    def merge_roads(road1: pd.Series, road2: pd.Series, update_nodes_immediately=True):
        assert isinstance(road1, pd.Series)
        assert isinstance(road2, pd.Series)
        if road1['level'] != road2['level']:
            logging.debug('[!]不同level的道路无法合并')
            return
        if road1['state'] != road2['state']:
            logging.debug('[!]不同state的道路无法合并')
            return
        coords1 = road1['coords']
        coords2 = road2['coords']
        if len(coords1) <= 1 or len(coords2) <= 1:
            logging.debug('只有一个点的道路暂不支持合并')
            return
        node_uids = {road1['u'], road1['v'], road2['u'], road2['v']}
        if len(node_uids) >= 4:
            logging.debug('没有找到共享的node， 无法合并')
            return
        if len(node_uids) <= 2:
            logging.debug('道路完全重合')
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
    def simplify_roads():
        org_nodes = Road.__node_gdf.copy()  # 这里必须创建一份副本，否则对node 的删改会改变列表
        org_node_count = len(org_nodes)
        for node_uid, node in org_nodes.iterrows():
            roads = Road.get_roads_by_node(node)
            if len(roads) == 2:
                Road.merge_roads(roads.iloc[0], roads.iloc[1])
        curr_node_count = len(Road.__node_gdf)
        logging.info(
            f'simplify_roads 结果：{org_node_count - curr_node_count}节点被优化, 优化后节点数: {curr_node_count}')

    @staticmethod
    def examine_invalid_roads() -> list[uuid.UUID]:
        invalids_road_uids = []
        for road_uid, road in Road.__edge_gdf.iterrows():
            road_uid: uuid.UUID = road_uid
            geo = road['geometry']
            if not isinstance(geo, LineString):
                invalids_road_uids.append(road_uid)
                continue
            length = geo.length
            if length < 1.0 / PRECISION * 2:
                invalids_road_uids.append(road_uid)
                continue
        return invalids_road_uids


    @staticmethod
    def auto_fix():
        logging.info('正在执行自动修复程序')
        # merge nodes
        Road.merge_all_close_nodes()
        Road.delete_roads_by_uids_list(Road.examine_invalid_roads())
        count = 0
        while True:
            a, b = Road.detect_intersection(Road.get_all_roads(), Road.get_all_roads())
            if len(a) == 0: break  # no intersection
            Road.split_roads_by_intersection_data(a, b)
            Road.merge_all_close_nodes()
            Road.delete_roads_by_uids_list(Road.examine_invalid_roads())
            count += 1
            if count > 10:
                logging.warning('达到最大清理循环上限，依旧检测到相交道路，请手动检查')
                break
        Road.simplify_roads()
        logging.info(f"自动修复完成, 共计{count}轮")

    # endregion

    # region 绘图相关
    @staticmethod
    def get_vertices_data_legacy(roads, style_factory):
        # time logger
        start_time = time.time()
        # colors and width
        params = style_factory(roads)  # tuple( colors and widths)
        in_colors = np.array(params[0], dtype=np.float32)  # float32
        in_widths = np.array(params[1], dtype=np.float32) * g.LINE_WIDTH_SCALE  # width multiplier  float32
        if in_colors.shape[1] == 3:
            in_colors = np.concatenate((in_colors, np.ones((len(in_colors), 1), dtype=np.float32)), axis=1)
        # coords, first and num
        vertex_coords = roads['coords']  # pandas
        in_first = np.concatenate(([0], np.cumsum(vertex_coords.apply(len).to_numpy()[:-1]))).astype(np.int32)  # int32
        in_num = vertex_coords.apply(len).to_numpy().astype(np.int32)  # int32
        in_vertex_coords = np.concatenate(vertex_coords.values, axis=0).astype(np.int32)  # (n, 2) int32

        # convert to bytes
        in_vertex_coords = in_vertex_coords.tobytes()  # 4 + 4 bytes
        in_first = in_first.tobytes()  # 4 byte
        in_num = in_num.tobytes()  # 4 bytes
        in_colors = in_colors.tobytes()  # 4 + 4 + 4 + 4  bytes
        in_widths = in_widths.tobytes()  # 4 bytes

        # time logger
        logging.debug(f'prepare bytes 消耗时间 = {time.time() - start_time}s')
        start_time = time.time()

        # c# code
        buffer = cAccelerator.TriangulatePolylines(in_vertex_coords, in_first, in_num, in_colors, in_widths)

        # time logger
        logging.debug(f'c# 代码消耗时间 = {time.time() - start_time}s')
        start_time = time.time()

        # convert to numpy
        vertices = np.frombuffer(bytes(buffer), np.float32).reshape(-1, 6)
        if np.any(np.isnan(vertices)):
            logging.warning("There are NaN values in the vertices array.")

        # time logger
        logging.debug(f'转换为numpy消耗时间 = {time.time() - start_time}s')
        return vertices

    @staticmethod
    def get_vertices_data(roads, style_factory):
        # time logger
        start_time = time.time()
        # colors and width
        params = style_factory(roads)  # tuple( colors and widths)
        colors = np.array(params[0], dtype=np.float32)  # float32
        in_widths = np.array(params[1], dtype=np.float32) * g.LINE_WIDTH_SCALE  # width multiplier  float32
        if colors.shape[1] == 3:
            colors = np.concatenate((colors, np.ones((len(colors), 1), dtype=np.float32)), axis=1)
        in_r, in_g, in_b, in_a = colors[:, 0].copy(), colors[:, 1].copy(), colors[:, 2].copy(), colors[:, 3].copy()

        # coords, first and num
        vertex_coords = roads['coords']  # pandas
        in_first = np.concatenate(([0], np.cumsum(vertex_coords.apply(len).to_numpy()[:-1])), dtype=np.int32)  # int32
        in_num = vertex_coords.apply(len).to_numpy().astype(np.int32)  # int32
        vertex_coords = np.concatenate(vertex_coords.values, axis=0).astype(np.float32)  # (n, 2) float32
        in_x, in_y = vertex_coords[:, 0].copy(), vertex_coords[:, 1].copy()
        # time logger
        logging.debug(f'prepare bytes 消耗时间 = {time.time() - start_time}s')
        start_time = time.time()

        # c# code
        c_params = arrs_addr_len(in_x, in_y, in_first, in_num, in_r, in_g, in_b, in_a, in_widths)
        buffer = cAccelerator.TriangulatePolylines(*c_params)

        # time logger
        logging.debug(f'c# 代码消耗时间 = {time.time() - start_time}s')
        start_time = time.time()

        # convert to numpy
        vertices = np.frombuffer(bytes(buffer), np.float32).reshape(-1, 6)
        if np.any(np.isnan(vertices)):
            logging.warning("There are NaN values in the vertices array.")

        # time logger
        logging.debug(f'转换为numpy消耗时间 = {time.time() - start_time}s')
        return vertices

    @staticmethod
    def get_node_vertices_data_legacy(nodes: gpd.GeoDataFrame, style_factory):
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

    @staticmethod
    def get_node_vertices_data(nodes: gpd.GeoDataFrame, style_factory):
        try:
            params = style_factory(nodes)
            in_widths = np.array(params[1], dtype=np.float32) * g.LINE_WIDTH_SCALE  # width multiplier
            colors = np.array(params[0], dtype=np.float32)
            if colors.shape[1] == 3:
                colors = np.concatenate((colors, np.ones((len(colors), 1), dtype=np.float32)), axis=1)
            in_r, in_g, in_b, in_a = colors[:, 0].copy(), colors[:, 1].copy(), colors[:, 2].copy(), colors[:, 3].copy()
            vertex_coords = np.concatenate(nodes['coord'].apply(np.array).values, axis=0).astype(np.float32).reshape(-1, 2)
            in_x, in_y = vertex_coords[:, 0].copy(), vertex_coords[:, 1].copy()

            # c# code
            c_params = arrs_addr_len(in_x, in_y, in_r, in_g, in_b, in_a, in_widths)
            buffer = cAccelerator.TriangulatePoints(*c_params)

            vertices = np.frombuffer(bytes(buffer), np.float32).reshape(-1, 6)
            return vertices
        except Exception as e:
            print(nodes.columns)
            raise e

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
