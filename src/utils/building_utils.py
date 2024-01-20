from enum import Enum
from gui.components import imgui_item_selector_component


class BuildingMovableType(Enum):
    NONDEMOLISHABLE = 0
    FLEXABLE = 1
    DEMOLISHABLE = 2
    UNDEFINED = -1


class BuildingStyle(Enum):
    HERITAGE = 0
    HISTORICAL = 1
    TRADITIONAL = 2
    NORMAL = 3
    UNDEFINED = -1


class BuildingQuality(Enum):
    GOOD = 0
    FAIR = 1
    POOR = 2
    UNDEFINED = -1


class BuildingCluster:
    def __init__(self):
        self.cluster = {'movable': {key: True for key in BuildingMovableType},
                        'style': {key: True for key in BuildingStyle},
                        'quality': {key: True for key in BuildingQuality}}

    def show_imgui_cluster_editor_button(self):
        any_change = False
        any_change |= imgui_item_selector_component('movable cluster >', self.cluster['movable'])
        any_change |= imgui_item_selector_component('style cluster >', self.cluster['style'])
        any_change |= imgui_item_selector_component('quality cluster >', self.cluster['quality'])
        return any_change
