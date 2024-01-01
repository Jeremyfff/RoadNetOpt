import os.path
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from geo import Road, Building, Object
from utils import point_utils, image_utils, road_utils, RoadState, RoadLevel, BuildingType

from optimize_module import RoadOptimizer
from fields import BuildingField, AttractionField, DirectionField, MomentumField, RandomField


def plot_obj(obj=None, output_folder=None, epoch=None, show_values=False):
    Object.plot_all()

    try:
        obj.plot()
    except Exception as e:
        pass
    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()
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


if __name__ == '__main__':
    main()

