import numpy as np
import matplotlib.pyplot as plt
import time
import shapely.plotting
from shapely.geometry import Polygon, LineString, Point
import networkx as nx
from geo import Object
from utils import RoadLevel, RoadState, BuildingType, point_utils, polyline_utils, road_utils
import style_module
import osmnx as ox


class Road(Object):
    __all_roads = set()

    def __init__(self, points: np.ndarray = None, level=RoadLevel.MAIN, state=RoadState.RAW):
        super().__init__()
        Road.register(self)
        # graph related

        # geometry related
        self.points = points

        self.level = level
        self.state = state

        self._search_space = None
        self._rewards = None

    def plot(self, *args, **kwargs):
        if self.points.shape[0] < 2:
            return
        super(Road, self).plot(*args, **kwargs)

        _style = style_module.get_road_style(self)
        line = LineString(self.points)
        shapely.plotting.plot_line(line, **_style)

    def add_point(self, point):
        self.points = np.append(self.points, [point], axis=0)

    def pop_point(self):
        return self.points.pop()

    def get_last_point(self):
        return self.points[-1]

    def get_last_vector(self):
        if self.points is None or self.points.shape[0] < 2:
            return np.array([0, 0])
        else:
            return point_utils.normalize_vector(self.points[-1] - self.points[-2])

    def interpolate(self, t):
        return polyline_utils.interpolate_by_t(self.points, t)

    @staticmethod
    def register(obj):
        Road.__all_roads.add(obj)

    @staticmethod
    def plot_all(*args, **kwargs):
        for road in Road.__all_roads:
            road.plot(*args, **kwargs)

    @staticmethod
    def get_all_roads():
        return Road.__all_roads

    @staticmethod
    def delete_all_roads():
        Road.__all_roads = set()

    @staticmethod
    def quick_roads():
        points = np.array([
            [0, 0],
            [0, 100],
            [-20, 20],
            [120, 20],
            [0, 20]
        ])
        road1 = Road(np.array([points[0], points[4]]), RoadLevel.MAIN)
        road2 = Road(np.array([points[4], points[1]]), RoadLevel.MAIN)
        road3 = Road(np.array([points[2], points[4]]), RoadLevel.SECONDARY)
        road4 = Road(np.array([points[4], points[3]]), RoadLevel.SECONDARY)
        return [road1, road2, road3, road4]

    @staticmethod
    def roads_to_graph(roads):
        start_time = time.time()
        point_set = set()
        start_points = [tuple(road.points[0]) for road in roads]
        end_points = [tuple(road.points[-1]) for road in roads]

        for i, road in enumerate(list(roads)):
            point_set.add(start_points[i])
            point_set.add(end_points[i])

        point_list = list(point_set)
        mapper = {point: idx for idx, point in enumerate(point_list)}
        G = nx.Graph()

        for i, point in enumerate(point_list):
            G.add_node(i, x=point[0], y=point[1], geometry=Point(point[0], point[1]))

        for i, road in enumerate(list(roads)):
            line = LineString(road.points)
            length = line.length
            G.add_edge(mapper[start_points[i]], mapper[end_points[i]],
                       name="",
                       length=length,
                       geometry=line,
                       level=road.level,
                       state=road.state)
        end_time = time.time()
        print(f"roads_to_graph 转换耗时 {(end_time - start_time) * 1000} ms")
        return G

    @staticmethod
    def graph_to_roads(G):
        roads = set()
        for u, v, data in G.edges.data():
            if 'geometry' in data:
                geometry: LineString = data['geometry']
            else:
                print("bad data")
                continue
            if 'level' in data:
                level = data['level']
            elif 'highway' in data:
                level = road_utils.highway_to_level(highway=data['highway'])
            else:
                level = RoadLevel.CUSTOM
            if 'state' in data:
                state = data['state']
            else:
                state = RoadState.RAW
            road = Road(points=np.array(geometry.coords), level=level, state=state)
            roads.add(road)
        return roads


def example_roads_to_graph():
    existed_roads = Road.quick_roads()
    G = Road.roads_to_graph(existed_roads)
    # 提取节点的坐标信息
    pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
    # 创建一个空字典，用于存储每条边的粗细
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
    Road.delete_all_roads()
    roads = Road.graph_to_roads(G)
    Road.plot_all()

    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # example_roads_to_graph()
    example_graph_to_roads()
