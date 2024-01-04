import os.path
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


def init_canvas():
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    fig, ax = plt.subplots()
    ax.set_frame_on(False)  # 没有边框
    ax.set_xticks([])  # 没有 x 轴坐标
    ax.set_yticks([])  # 没有 y 轴坐标
    ax.set_aspect('equal')  # 横纵轴比例相同
    fig.tight_layout()
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


def example_load_data():
    from descartes import PolygonPatch
    import geopandas as gpd

    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)
    Road.show_info()
    # Building.data_to_buildings(data)
    # Region.data_to_regions(data)

    canvas, ax = init_canvas()
    Road.plot_all(ax=ax)
    road = Road.get_last_road()
    Road.split_road(road, 0.5, True)
    Road.show_info()
    canvas.draw()
    # 从画布中提取图像数据为 NumPy 数组
    image_data = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
    image_data = image_data.reshape(canvas.get_width_height()[::-1] + (3,))
    # 创建 PIL 的图像对象
    pil_image = Image.fromarray(image_data)
    # 显示图像
    pil_image.show()


def example_graph():
    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)
    fig, ax = init_plt()
    G = Road.to_graph()
    pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
    nx.draw_networkx(G,
                     ax=ax,
                     pos=pos,
                     with_labels=False,
                     node_size=10)  # 绘制图形
    plt.show()  # 显示图形


def simplify_roads_example():
    data = io_utils.load_data("../data/和县/data.bin")
    Road.data_to_roads(data)
    Road.simplify_roads()
    Road.show_info()

if __name__ == '__main__':
    simplify_roads_example()
