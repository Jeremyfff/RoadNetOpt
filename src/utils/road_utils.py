import time
import matplotlib.pyplot as plt
from enum import Enum
import pandas as pd
import imgui
from utils.common_utils import imgui_item_selector_component

class RoadLevel(Enum):
    MAIN = 0
    SECONDARY = 1
    BRANCH = 2
    ALLEY = 3
    CUSTOM = 4
    UNDEFINED = -1


class RoadState(Enum):
    RAW = 0
    OPTIMIZED = 1
    OPTIMIZING = 2


all_highway_types = {'service', 'residential', 'footway', 'secondary', 'pedestrian', 'primary',
                     'tertiary', 'trunk', 'unclassified', 'secondary_link', 'busway', 'steps', 'cycleway'}

main_types = {'trunk', 'primary'}
secondary_types = {'secondary'}
branch_types = {'tertiary'}
alley_types = {'residential', 'footway', 'cycleway', 'steps', 'pedestrian'}


def highway_to_level(highway):
    if highway in main_types:
        return RoadLevel.MAIN
    elif highway in secondary_types:
        return RoadLevel.SECONDARY
    elif highway in branch_types:
        return RoadLevel.BRANCH
    elif highway in alley_types:
        return RoadLevel.ALLEY
    else:
        return RoadLevel.CUSTOM





class RoadCluster:
    def __init__(self):
        self.cluster = {'level': {key: True for key in RoadLevel}, 'state': {key: True for key in RoadState}}

    def show_imgui_cluster_editor_button(self):
        any_change = False
        any_change |= imgui_item_selector_component('road level cluster', self.cluster['level'])
        any_change |= imgui_item_selector_component('road state cluster', self.cluster['state'])
        return any_change
