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
from lib.accelerator import *
from gui import global_var as g
from sklearn.cluster import DBSCAN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class Road(Object):

    @staticmethod
    def uid():
        return cRoadManager.uuid

    @staticmethod
    def clear_unused_nodes():
        cNodeManager.ClearUnusedNodes()

    @staticmethod
    def get_all_nodes():
        return cNodeManager.GetAllNodes()

    @staticmethod
    def get_close_nodes(eps=0.1, min_samples=2):
        """
        :param eps: 领域的大小
        :param min_samples: 领域内最小样本数, 默认为2
        :return:
        """
        cCoords = cNodeManager.GetAllNodeCoords()
        buffer = bytes(cCommon.CoordsToNumpy(cCoords))
        coords = np.frombuffer(buffer, dtype=np.float32).reshape(-1, 2)
        # 从向量数组或距离矩阵执行 DBSCAN 聚类。
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(coords)
        labels = np.array(labels)
        group = cNodeManager.GetCloseNodesGroup(*arrs_addr_len(labels))
        return group

    @staticmethod
    def merge_grouped_nodes(group):
        cNodeManager.MergeGroupedNodes(group)

    # endregion

    # region 创建删除
    @staticmethod
    def add_road_by_coords(coords: np.ndarray,
                           level: RoadLevel,
                           state: RoadState):
        cCoords = coords_to_cCoords(coords)
        return cRoadManager.AddRoad(cCoords, level.value, state.value)

    @staticmethod
    def add_roads_by_coords(coords_list: list[np.ndarray],
                            levels_list: list[RoadLevel],
                            states_list: list[RoadState]):
        """通过坐标创建roads并添加至Road.__edge_gdf"""

        for i in range(len(coords_list)):
            Road.add_road_by_coords(coords_list[i], levels_list[i], states_list[i])

    @staticmethod
    def remove_road(road):
        cRoadManager.RemoveRoad(road)

    @staticmethod
    def remove_all_roads():
        cRoadManager.RemoveAllRoads()

    # endregion

    # region 获取查找
    @staticmethod
    def get_road_by_uid(uid):
        assert isinstance(uid, cGuidType)
        road = cRoadManager.GetRoadByUid(uid)
        return road

    @staticmethod
    def get_road_by_index(idx):
        return cRoadManager.GetRoadByIndex(idx)

    @staticmethod
    def get_roads_by_indexes(idx_list: list[int]):
        idx_list = int_list_to_cIntArr(idx_list)
        return cRoadManager.GetRoadsByIndexes(idx_list)

    @staticmethod
    def get_roads_by_attr_and_value(attr: str, value: Union[RoadLevel, RoadState]):
        if attr == 'level':
            return cRoadManager.GetRoadsByLevel(RoadLevel(value).value)
        elif attr == 'state':
            return cRoadManager.GetRoadsByState(RoadState(value).value)
        else:
            raise Exception

    @staticmethod
    def get_all_roads():
        return cRoadManager.GetAllRoads()

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
    def get_valid_spawn_range(road):
        """求可以生成新路的位置，如果没有，返回None"""
        cLineString = road.lineString
        dist_threshold = road_utils.distance_threshold_by_road_level[RoadLevel(road.GetIntLevel())]
        if cLineString.Length < 2 * dist_threshold:
            return None, None
        return dist_threshold, cLineString.Length - dist_threshold

    @staticmethod
    def get_road_last_coord(road):
        return road.GetLastCoord()

    @staticmethod
    def get_road_last_vector(road):
        return road.GetLastVector()

    # endregion

    # region 编辑修改
    @staticmethod
    def update_coords(road, cCoords):
        return road.UpdateCoords(cCoords)

    @staticmethod
    def add_u_node(road, node):
        return road.AddUNode(node)

    @staticmethod
    def add_v_node(road, node):
        return road.AddVNode(node)

    @staticmethod
    def replace_u_node(road, node):
        return road.ReplaceUNode(node)

    @staticmethod
    def replace_v_node(road, node):
        return road.ReplaceVNode(node);

    @staticmethod
    def interpolate_road(road, distance, normalized):
        return cRoadManager.InterpolateRoad(road, distance, normalized)

    @staticmethod
    def split_road(road, distance, normalized):
        return cRoadManager.SplitRoad(road, distance, normalized)

    @staticmethod
    def split_road_by_coord(road, cCoord):
        return cRoadManager.SplitRoad(road, cCoord)

    @staticmethod
    def split_road_by_random_position(road):
        """随机选取一个位置作为新路的出生点，并且将路进行分割， 返回分割点"""


    @staticmethod
    def merge_roads(road1, road2):
       return cRoadManager.MergeRoads(road1, road2)
    @staticmethod
    @timer
    def simplify_roads():
        cRoadManager.SimplifyAllRoads()

    # endregion

    # region 绘图相关

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
