from enum import Enum
from gui.components import imgui_item_selector_component


class RegionAccessibleType(Enum):
    ACCESSIBLE = 0
    RESTRICTED = 1
    INACCESSIBLE = 2
    UNDEFINED = -1


class RegionType(Enum):
    ARTIFICIAL = 0
    WATER = 1
    BOUNDARY = 2
    UNDEFINED = -1


class RegionCluster:
    def __init__(self):
        self.cluster = {'accessible': {key: True for key in RegionAccessibleType},
                        'region_type': {key: True for key in RegionType}}

    def show_imgui_cluster_editor_button(self):
        any_change = False
        any_change |= imgui_item_selector_component('accessible cluster >', self.cluster['accessible'])
        any_change |= imgui_item_selector_component('region type cluster >', self.cluster['region_type'])
        return any_change
