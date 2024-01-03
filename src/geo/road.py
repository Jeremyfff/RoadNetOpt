import numpy as np
import matplotlib.pyplot as plt
import time
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


class Road(Object):
    """
    这个版本的Road代码是纯手写的，还没有经过测试
    """
    __node_attrs = ['uid', 'x', 'y', 'geometry', 'cache']
    __edge_attrs = ['u', 'v', 'uid', 'geometry', 'level', 'state', 'cache']

    __node_gdf = gpd.GeoDataFrame(columns=__node_attrs)
    __node_gdf.set_index('uid')

    __edge_gdf = gpd.GeoDataFrame(columns=__edge_attrs)
    __edge_gdf.set_index('uid')

    __cached_graph = None
    __cached_node_gdf = None
    __cached_edge_gdf = None

    _flag_cached_graph_need_update = False

    # region 节点相关

    @staticmethod
    def _create_node(uid, x, y, geometry):
        new_row = {'geometry': [geometry],
                   'x': [x],
                   'y': [y],
                   'uid': [uid]
                   }
        new_gdf = gpd.GeoDataFrame(new_row, index=new_row['uid'])
        Road.__node_gdf = gpd.pd.concat([Road.__edge_gdf, new_gdf], ignore_index=False)

    @staticmethod
    def _create_nodes(uid_list, x_list, y_list, geometry_list):
        new_row = {'geometry': geometry_list,
                   'x': x_list,
                   'y': y_list,
                   'uid': uid_list
                   }
        new_gdf = gpd.GeoDataFrame(new_row, index=new_row['uid'])
        Road.__node_gdf = gpd.pd.concat([Road.__edge_gdf, new_gdf], ignore_index=False)

    @staticmethod
    @jit(nopython=True)
    def _node_uid_from_coord(coord: Union[list, tuple, np.ndarray]) -> uuid.UUID:
        point = Point(coord)
        is_in_gdf = Road.__node_gdf.geometry.contains(point)
        if is_in_gdf.any():
            # use existed node
            matching_rows = Road.__node_gdf[is_in_gdf]
            return matching_rows['uid']
        else:
            # create a new node
            uid = uuid.uuid4()
            coords = point.coords.xy
            x = coords[0]
            y = coords[1]
            Road._create_node(uid, x, y, point)
            return uid

    @staticmethod
    def _get_nodes_by_roads(roads):
        """返回被roads引用的所有node"""
        nodes = Road.__node_gdf[Road.__node_gdf['uid'].isin(roads['u']) | Road.__node_gdf['uid'].isin(roads['v'])]
        return nodes

    @staticmethod
    def _any_road_using_node(uid):
        return any(Road.__edge_gdf['u'].eq(uid)) or any(Road.__edge_gdf['v'].eq(uid))

    # endregion

    # region 创建删除
    @staticmethod
    def create_road_by_coords(coords: np.ndarray,
                              level: RoadLevel,
                              state: RoadState):
        geometry = point_utils.points_to_geo(coords)
        return Road.create_road_by_geometry(geometry, level, state)

    @staticmethod
    def create_road_by_geometry(geometry: Union[LineString, Point],
                                level: RoadLevel,
                                state: RoadState):
        # 注意，虽然创建的road没有加到Road的edge gdf中，但这里的节点将直接加到Road的node gdf中
        u = Road._node_uid_from_coord(geometry.coords[0])
        v = Road._node_uid_from_coord(geometry.coords[-1])
        uid = uuid.uuid4()
        new_row = {'u': u,
                   'v': v,
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
        u_list = [Road._node_uid_from_coord(geom.coords[0]) for geom in geometry_list]
        v_list = [Road._node_uid_from_coord(geom.coords[-1]) for geom in geometry_list]
        uid_list = [uuid.uuid4() for _ in range(len(geometry_list))]
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
        Road.__edge_gdf = gpd.pd.concat([Road.__edge_gdf, road], ignore_index=False)
        return road['uid']

    @staticmethod
    def add_roads(roads):
        Road.__edge_gdf = gpd.pd.concat([Road.__edge_gdf, roads], ignore_index=False)
        return list(roads['uid'])

    @staticmethod
    def add_road_by_coords(coords: np.ndarray,
                           level: RoadLevel,
                           state: RoadState):
        road = Road.create_road_by_coords(coords, level, state)
        return Road.add_road(road)

    @staticmethod
    def _add_road_by_geometry(geometry: Union[LineString, Point],
                              level: RoadLevel,
                              state: RoadState) -> uuid.UUID:
        road = Road.create_road_by_geometry(geometry, level, state)
        return Road.add_road(road)

    @staticmethod
    def add_roads_by_coords(points_list: list[np.ndarray],
                            levels_list: list[RoadLevel],
                            states_list: list[RoadState]) -> list[uuid.UUID]:
        roads = Road.create_roads_by_coords(points_list , levels_list, states_list)
        return Road.add_roads(roads)

    @staticmethod
    def _add_roads_by_geometries(geometry_list: list[LineString, Point],
                                 levels_list: list[RoadLevel],
                                 states_list: list[RoadState]) -> list[uuid.UUID]:
        roads = Road.create_roads_by_geometries(geometry_list, levels_list, states_list)
        return Road.add_roads(roads)

    @staticmethod
    def delete_road(road, update_nodes_immediately=True):
        uid = road['uid']
        u = road['u']
        v = road['v']

        Road.__edge_gdf.drop(uid)

        # handle cache
        if road['cache']:
            Road._flag_cached_graph_need_update = True

        # delete unused nodes
        if update_nodes_immediately:
            if not Road._any_road_using_node(u):
                Road.__node_gdf.drop(u)
            if not Road._any_road_using_node(v):
                Road.__node_gdf.drop(v)

    @staticmethod
    def delete_road_by_uid(uid, update_nodes_immediately=True):
        Road.delete_road(Road.get_road_by_uid(uid), update_nodes_immediately)

    @staticmethod
    def delete_all(clear_cache=True):
        """清空所有内容"""
        Road.__edge_gdf = Road.__edge_gdf.drop(Road.__edge_gdf['uid'])
        Road.__node_gdf = Road.__node_gdf.drop(Road.__node_gdf['uid'])
        if clear_cache:
            Road.clear_cache()

    # endregion

    # region 获取查找
    @staticmethod
    def get_road_by_uid(uid: uuid.UUID):
        road = Road.__edge_gdf.loc[uid]
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
    def get_last_road():
        last_road = Road.__edge_gdf.iloc[-1]
        return last_road

    @staticmethod
    def get_all_roads():
        return Road.__edge_gdf

    # endregion

    # region 编辑修改
    @staticmethod
    def add_point_to_road(road, point: np.ndarray):
        if len(point.shape) == 1:
            point = np.unsqueeze(point, axis=0)
        Road.add_points_to_road(road, point)

    @staticmethod
    def update_road_points(road, points: np.ndarray, update_nodes_immediately=True):
        assert len(points.shape) == 2
        assert points.shape[0] >= 2
        uid = road['uid']
        org_geo = road['geometry']
        org_u = Road._node_uid_from_coord(org_geo.coords[0])
        org_v = Road._node_uid_from_coord(org_geo.coords[-1])

        new_points = points
        new_geo = LineString(new_points)
        new_u = Road._node_uid_from_coord(new_geo.coords[0])
        new_v = Road._node_uid_from_coord(new_geo.coords[-1])

        Road.__edge_gdf.at[uid, 'geometry'] = new_geo
        Road.__edge_gdf.at[uid, 'u'] = new_u
        Road.__edge_gdf.at[uid, 'v'] = new_v
        # handle org nodes
        if update_nodes_immediately:
            if not Road._any_road_using_node(org_u):
                Road.__node_gdf.drop(org_u)
            if not Road._any_road_using_node(org_v):
                Road.__node_gdf.drop(org_v)
        # handle cache
        if road['cache']:
            Road._flag_cached_graph_need_update = True

    @staticmethod
    def add_points_to_road(road, points: np.ndarray, update_nodes_immediately=True):
        assert len(points.shape) == 2
        org_geo = road['geometry']
        org_points = np.array(list(org_geo.coords))
        new_points = np.vstack([org_points, points])
        Road.update_road_points(road, new_points, update_nodes_immediately)

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
            return np.array(cut_point.coords)
        assert len(new_geos) == 2
        Road._add_road_by_geometry(new_geos[0], level=level, state=state)
        Road._add_road_by_geometry(new_geos[1], level=level, state=state)
        Road.delete_road(road, update_nodes_immediately)  # org nodes will be handled here
        # handle cache
        if road['cache']:
            Road._flag_cached_graph_need_update = True
        return np.array(list(cut_point.coords))

    # endregion

    # region 绘图相关
    @staticmethod
    def plot_all(*args, **kwargs):
        """使用geo pandas进行加速绘制"""
        Road.__edge_gdf.plot(*args, **kwargs)

    # endregion

    # region 类型转换
    @staticmethod
    @jit(nopython=False)
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
    def data_to_roads(data: dict):
        assert 'roads' in data, 'invalid data'
        roads_data = data['roads']
        points_list = []
        level_list = []
        state_list = []
        for road_data in roads_data:
            points_list.append(np.array(road_data['points']))
            level_list.append(road_data['level'])
            state_list.append(road_data['state'])
        uid_list = Road.add_roads_by_coords(points_list, level_list, state_list)
        return uid_list

    @staticmethod
    def roads_to_data(out_data: dict):
        if 'roads' not in out_data:
            out_data['roads'] = []
        for road in Road.get_all_roads():
            road_data = {
                'points': np.array(list(road['geometry'].coords)),
                'level': road.level,
                'state': road.state
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
        else:
            logging.warning("no cache to restore")
    # endregion


def example_roads_to_graph():
    raise NotImplementedError
    existed_roads = Road.quick_roads()
    G = Road.to_graph(existed_roads)

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
    raise NotImplementedError
    G = ox.graph_from_bbox(37.79, 37.78, -122.41, -122.43, network_type='drive')
    Road.delete_all_roads()
    roads = Road.from_graph(G)
    Road.plot_all()

    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # example_roads_to_graph()
    # example_graph_to_roads()
    point = Point([0, 1])
    line_string = LineString([[0, 0], [1, 2]])

    print(np.array(list(line_string.coords)).shape)


