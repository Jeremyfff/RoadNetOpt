import os.path
import random

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from geo import Road, Building, Region, Object
from utils import point_utils, image_utils, road_utils, io_utils
from utils import RoadState, RoadLevel

from optimize_module import RoadOptimizer
from fields import BuildingField, AttractionField, DirectionField, MomentumField, RandomField


def init_plt():
    fig, ax = plt.subplots()
    ax.set_frame_on(False)  # 没有边框
    ax.set_xticks([])  # 没有 x 轴坐标
    ax.set_yticks([])  # 没有 y 轴坐标
    ax.set_aspect('equal')  # 横纵轴比例相同
    fig.tight_layout()
    return fig, ax


def init_canvas(figsize=(8, 8), dpi=100):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    plt.clf()
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_frame_on(True)  # 没有边框
    ax.set_xticks([])  # 没有 x 轴坐标
    ax.set_yticks([])  # 没有 y 轴坐标
    ax.set_aspect('equal')  # 横纵轴比例相同
    fig.tight_layout()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    canvas = FigureCanvas(fig)
    return canvas, ax


def plot_obj(obj=None, output_folder=None, epoch=None, show_values=False):
    Object.plot_all()

    try:
        obj.plot()
    except Exception as e:
        pass

    if output_folder is not None:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        plt.savefig(os.path.join(output_folder, f"{epoch}_{obj.name}.jpg"))
    else:
        plt.show()
    plt.clf()


def main():
    output_folder = "output"

    # generate roads and buildings
    existed_roads = Road.quick_roads()
    existed_buildings = Building.quick_buildings()

    # define static search space
    point_grid = point_utils.point_grid(0, 0, 100, 100, 5)

    # define fields
    building_field = BuildingField()
    attract_points = np.array([[99, 0], [56, 89]])
    attract_field = AttractionField(attract_points)
    attract_field.weight = 3
    direction_field = DirectionField()
    direction_field.weight = 0.2
    momentum_field = MomentumField()
    random_field = RandomField()
    all_fields = [building_field, attract_field, direction_field, momentum_field, random_field]

    # generate a new road
    start_point = existed_roads[0].interpolate(0.4)
    new_road = Road(np.array([start_point]),
                    level=RoadLevel.BRANCH,
                    state=RoadState.OPTIMIZING)

    # define optimizer for this road
    optimizer = RoadOptimizer(new_road, all_fields)

    # optimize
    for epoch in range(10):
        print(f"epoch {epoch}")
        optimizer.clear_rewards()
        optimizer.get_rewards(point_grid)
        optimizer.step()
        # plotting
        plot_obj(optimizer, output_folder, epoch, show_values=False)
        for field in all_fields:
            plot_obj(field, output_folder, epoch)

    # end of optimization
    new_road.state = RoadState.OPTIMIZED


def example_data_to_roads():
    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)
    Road.show_info()


def example_data_to_all():
    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)
    Building.data_to_buildings(data)
    Region.data_to_regions(data)

    Road.get_all_roads()
    Building.get_all_buildings()
    Region.get_all_regions()


def example_road_to_graph():
    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)
    fig, ax = init_plt()
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
    nx.draw_networkx(G,
                     ax=ax,
                     pos=pos,
                     width=[edge_width[e] for e in G.edges()],
                     with_labels=False,
                     node_size=10)  # 绘制图形
    plt.show()  # 显示图形


def example_simplify_roads():
    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)
    Road.simplify_roads()
    Road.show_info()


def example_buildings_from_data():
    data = io_utils.load_data("../data/和县/data.bin")
    Building.data_to_buildings(data)
    fig, ax = init_plt()
    Building.plot_all(ax=ax)
    plt.show()


def example_plot_to_buffer():
    data = io_utils.load_data("../data/和县/data.bin")
    Building.data_to_buildings(data)
    Road.data_to_roads(data)
    canvas, ax = init_canvas(figsize=(8, 8))

    Building.plot_all(ax=ax)
    Road.plot_all(ax=ax)

    x_range = ax.get_xlim()
    x_min = x_range[0]
    x_max = x_range[1]
    y_range = ax.get_ylim()
    y_min = y_range[0]
    y_max = y_range[1]

    x_width = x_max - x_min
    y_width = y_max - y_min

    if x_width < y_width:
        x_center = (x_min + x_max) / 2
        x_range = (x_center - y_width / 2, x_center + y_width / 2)
    elif x_width > y_width:
        y_center = (y_min + y_max) / 2
        y_range = (y_center - x_width / 2, y_center + x_width / 2)
    ax.set_xlim(x_range)
    ax.set_ylim(y_range)

    canvas.draw()
    # 从画布中提取图像数据为 NumPy 数组
    image_data = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
    image_data = image_data.reshape(canvas.get_width_height()[::-1] + (4,))
    # 创建 PIL 的图像对象
    pil_image = Image.fromarray(image_data)
    # 显示图像
    pil_image.show()


def example_add_and_modify_road():
    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)

    print('Creating my road')
    # output: Creating my road
    my_road_start_point = np.array([[2, 3]])
    print(f'My road start point is {my_road_start_point}')
    # output: My road start point is [[2 3]]
    my_road_uid = Road.add_road_by_coords(coords=my_road_start_point, level=RoadLevel.BRANCH,
                                          state=RoadState.OPTIMIZING)

    my_road = Road.get_road_by_uid(my_road_uid)
    print(f'My road created (uid: {my_road_uid}, type: {type(my_road)})')
    # output: My road created (uid: fc3234e5-3b5a-4e1c-93de-5f590415e511, type: <class 'pandas.core.series.Series'>)
    print('My road geo: ', my_road['geometry'])
    # output: My road geo:  POINT (2 3)
    for i in range(5):
        new_point = np.random.rand(1, 2) * 10
        print(f'[{i}] new point = {new_point}')
        #  output: [0] new point = [[2.65889853 7.19537759]]
        #  output: [1] new point = [[0.20383911 1.77654136]]
        #  output: [2] new point = [[9.74504769 7.18593455]]
        #  output: [3] new point = [[5.7888099  2.07847427]]
        #  output: [4] new point = [[0.51628918 1.22321586]]
        my_road = Road.add_point_to_road(my_road, point=new_point)
        # 由于pd.Serial与元组的性质类似，对其任何的修改都会创建一个新的对象，
        # 因此这里add point的地方需要写my_road = Road.add_point_to_road(my_road, point=new_point)

    print('\nMy road geo: ', my_road['geometry'])
    # output: My road geo:  LINESTRING (2 3, 2.658898529150666 7.195377590750704, 0.2038391080744739 1.7765413565553279, 9.745047694992158 7.185934551413156, 5.788809902421127 2.0784742740679296, 0.5162891813906301 1.2232158625001954)
    print(np.array(list(my_road['geometry'].coords)))
    # output:
    # [[2.         3.        ]
    #  [2.65889853 7.19537759]
    #  [0.20383911 1.77654136]
    #  [9.74504769 7.18593455]
    #  [5.7888099  2.07847427]
    #  [0.51628918 1.22321586]]


if __name__ == '__main__':
    example_add_and_modify_road()
