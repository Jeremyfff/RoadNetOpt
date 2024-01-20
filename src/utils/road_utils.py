from enum import Enum

from gui.components import imgui_item_selector_component


class RoadLevel(Enum):
    TRUNK = 0
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3
    FOOTWAY = 4
    UNDEFINED = -1


class RoadState(Enum):
    RAW = 0
    MODIFIED = 1
    OPTIMIZED = 2
    OPTIMIZING = 3


#  路口距离阈值
distance_threshold_by_road_level = {
    RoadLevel.TRUNK: 80,
    RoadLevel.PRIMARY: 60,
    RoadLevel.SECONDARY: 40,
    RoadLevel.TERTIARY: 20,
    RoadLevel.FOOTWAY: 10,
    RoadLevel.UNDEFINED: 10
}

# osm 转换工具
all_highway_types = {'service', 'residential', 'footway', 'secondary', 'pedestrian', 'primary',
                     'tertiary', 'trunk', 'unclassified', 'secondary_link', 'busway', 'steps', 'cycleway'}

trunk_types = {'trunk'}
primary_types = {'primary'}
secondary_types = {'secondary'}
tertiary_types = {'tertiary'}
footway_types = {'residential', 'footway', 'cycleway', 'steps', 'pedestrian'}


def highway_to_level(highway):
    if highway in trunk_types:
        return RoadLevel.TRUNK
    elif highway in primary_types:
        return RoadLevel.PRIMARY
    elif highway in secondary_types:
        return RoadLevel.SECONDARY
    elif highway in tertiary_types:
        return RoadLevel.TERTIARY
    elif highway in footway_types:
        return RoadLevel.FOOTWAY
    else:
        return RoadLevel.UNDEFINED


class RoadCluster:
    def __init__(self):
        self.cluster = {'level': {key: True for key in RoadLevel}, 'state': {key: True for key in RoadState}}

    def show_imgui_cluster_editor_button(self):
        any_change = False
        any_change |= imgui_item_selector_component('level cluster >', self.cluster['level'])
        any_change |= imgui_item_selector_component('state cluster >', self.cluster['state'])
        return any_change
