import os.path

import matplotlib.pyplot as plt
import numpy as np
from geo import Road, Building, Geometry
from utils import point_utils, image_utils, road_utils, RoadState, RoadLevel, BuildingType

from optimize_module import RoadOptimizer
from fields import BuildingField, AttractionField, DirectionField, MomentumField


def init_plt():
    plt.axis('equal')
    plt.axis('off')
    plt.grid(False)
    plt.tight_layout()

def plot_field(field, output_folder, epoch):
    Geometry.plot_all()
    field.plot()
    init_plt()
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(os.path.join(output_folder, f"{epoch}_{field.name}.jpg"))
    plt.clf()

def main():
    output_folder = "output"

    existed_roads = Road.RandomRoads()
    existed_buildings = Building.RandomBuildings()

    point_grid = point_utils.point_grid(0, 0, 100, 100, 5)

    start_point = existed_roads[0].interpolate(0.4)
    second_point = start_point + np.array([5, 0])
    new_road = Road(np.array([start_point, second_point]),
                    level=RoadLevel.BRANCH,
                    state=RoadState.OPTIMIZING)

    building_field = BuildingField()
    attract_points = np.array([[99, 0], [56, 89]])
    attract_field = AttractionField(attract_points)
    attract_field.weight = 3
    direction_field = DirectionField()
    direction_field.weight = 0.2
    momentum_field = MomentumField()
    all_fields = [building_field, attract_field, direction_field, momentum_field]

    optimizer = RoadOptimizer(new_road, all_fields)

    for epoch in range(10):
        print(f"epoch {epoch}")
        optimizer.clear_rewards()
        optimizer.get_rewards(point_grid)
        optimizer.step()

        # plotting
        Geometry.plot_all()
        optimizer.plot()
        init_plt()
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        plt.savefig(os.path.join(output_folder, f"{epoch}_all.jpg"))
        plt.clf()
        # for field in all_fields:
        #    plot_field(field, output_folder, epoch)


if __name__ == '__main__':
    main()
