import imgui

from utils import RoadLevel, RoadState
from utils import BuildingMovableType, BuildingStyle, BuildingQuality
from utils import RegionAccessibleType


class PlotStyle:
    def __init__(self):
        self.ROAD_COLOR_BY_LEVEL = {
            RoadLevel.MAIN: (0, 0, 0),
            RoadLevel.SECONDARY: (0.2, 0.2, 0.2),
            RoadLevel.BRANCH: (0.4, 0.4, 0.4),
            RoadLevel.ALLEY: (0.6, 0.6, 0.6),
            RoadLevel.CUSTOM: (0, 0, 0),
        }

        self.ROAD_WIDTH_BY_LEVEL = {
            RoadLevel.MAIN: 5,
            RoadLevel.SECONDARY: 4,
            RoadLevel.BRANCH: 3,
            RoadLevel.ALLEY: 2,
            RoadLevel.CUSTOM: 1,
        }

        self.ROAD_COLOR_BY_STATE = {
            RoadState.RAW: (0, 0, 0),
            RoadState.OPTIMIZED: (0.2, 0.2, 0.2),
            RoadState.OPTIMIZING: (0.4, 0.4, 0.4),
        }
        self.ROAD_WIDTH_BY_STATE = {
            RoadState.RAW: 3,
            RoadState.OPTIMIZED: 3,
            RoadState.OPTIMIZING: 5,
        }

        self.BUILDING_COLOR_BY_MOVABLE_TYPE = {
            BuildingMovableType.NONDEMOLISHABLE: (0, 0, 0),
            BuildingMovableType.FLEXABLE: (0.2, 0.2, 0.2),
            BuildingMovableType.DEMOLISHABLE: (0.4, 0.4, 0.4),
            BuildingMovableType.UNDEFINED: (0.6, 0.6, 0.6)
        }
        self.BUILDING_COLOR_BY_STYLE = {
            BuildingStyle.HERITAGE: (0, 0, 0),
            BuildingStyle.HISTORICAL: (0.2, 0.2, 0.2),
            BuildingStyle.TRADITIONAL: (0.4, 0.4, 0.4),
            BuildingStyle.NORMAL: (0.6, 0.6, 0.6),
            BuildingStyle.UNDEFINED: (0.8, 0.8, 0.8),
        }

        self.BUILDING_COLOR_BY_QUALITY = {
            BuildingQuality.GOOD: (0, 0, 0),
            BuildingQuality.FAIR: (0.2, 0.2, 0.2),
            BuildingQuality.POOR: (0.4, 0.4, 0.4),
            BuildingQuality.UNDEFINED: (0.6, 0.6, 0.6)
        }

        self.REGION_COLOR_BY_ACCESSIBLE = {
            RegionAccessibleType.ACCESSIBLE: (0, 0, 0, 0.3),
            RegionAccessibleType.RESTRICTED: (0.2, 0.2, 0.2, 0.3),
            RegionAccessibleType.INACCESSIBLE: (0.4, 0.4, 0.4, 0.3),
            RegionAccessibleType.UNDEFINED: (0.6, 0.6, 0.6, 0.3)
        }
        self.REGION_COLOR_BY_TYPE = {
            RegionAccessibleType.ACCESSIBLE: (0, 0, 0, 0.3),
            RegionAccessibleType.RESTRICTED: (0.2, 0.2, 0.2, 0.3),
            RegionAccessibleType.INACCESSIBLE: (0.4, 0.4, 0.4, 0.3),
            RegionAccessibleType.UNDEFINED: (0.6, 0.6, 0.6, 0.3)
        }

        self.road_style_factory_dict = {'level': self.road_level_style_factory,
                                        'state': self.road_state_style_factory}

        self.building_style_factory_dict = {'movable': self.building_movable_style_factory,
                                            'style': self.building_style_style_factory,
                                            'quality': self.building_quality_style_factory}
        self.region_style_factory_dict = {'accessible': self.region_accessible_style_factory,
                                          'region_type': self.region_type_style_factory}

        self.current_road_style_name = 'level'
        self.current_building_style_name = 'movable'
        self.current_region_style_name = 'accessible'

    def road_level_style_factory(self, roads):
        colors, width = [], []
        for uid, road in roads.iterrows():
            colors.append(self.ROAD_COLOR_BY_LEVEL[road['level']])
            width.append(self.ROAD_WIDTH_BY_LEVEL[road['level']])
        return colors, width

    def road_state_style_factory(self, roads):
        colors, width = [], []
        for uid, road in roads.iterrows():
            colors.append(self.ROAD_COLOR_BY_STATE[road['state']])
            width.append(self.ROAD_WIDTH_BY_STATE[road['state']])
        return colors, width

    def building_movable_style_factory(self, buildings):
        colors, face_color, edge_color, line_width = [], [], [], []
        for uid, building in buildings.iterrows():
            colors.append(self.BUILDING_COLOR_BY_MOVABLE_TYPE[building['movable']])
            face_color.append(self.BUILDING_COLOR_BY_MOVABLE_TYPE[building['movable']])
            edge_color.append(self.BUILDING_COLOR_BY_MOVABLE_TYPE[building['movable']])
            line_width.append(None)
        return colors, face_color, edge_color, line_width

    def building_style_style_factory(self, buildings):
        colors, face_color, edge_color, line_width = [], [], [], []
        for uid, building in buildings.iterrows():
            colors.append(self.BUILDING_COLOR_BY_STYLE[building['style']])
            face_color.append(self.BUILDING_COLOR_BY_STYLE[building['style']])
            edge_color.append(self.BUILDING_COLOR_BY_STYLE[building['style']])
            line_width.append(None)
        return colors, face_color, edge_color, line_width

    def building_quality_style_factory(self, buildings):
        colors, face_color, edge_color, line_width = [], [], [], []
        for uid, building in buildings.iterrows():
            colors.append(self.BUILDING_COLOR_BY_QUALITY[building['quality']])
            face_color.append(self.BUILDING_COLOR_BY_QUALITY[building['quality']])
            edge_color.append(self.BUILDING_COLOR_BY_QUALITY[building['quality']])
            line_width.append(None)
        return colors, face_color, edge_color, line_width

    def region_accessible_style_factory(self, regions):
        colors, face_color, edge_color, line_width = [], [], [], []
        for uid, region in regions.iterrows():
            colors.append(self.REGION_COLOR_BY_ACCESSIBLE[region['accessible']])
            face_color.append(self.REGION_COLOR_BY_ACCESSIBLE[region['accessible']])
            edge_color.append(self.REGION_COLOR_BY_ACCESSIBLE[region['accessible']])
            line_width.append(1)
        return colors, face_color, edge_color, line_width

    def region_type_style_factory(self, regions):
        colors, face_color, edge_color, line_width = [], [], [], []
        for uid, region in regions.iterrows():
            colors.append(self.REGION_COLOR_BY_TYPE[region['type']])
            face_color.append(self.REGION_COLOR_BY_TYPE[region['type']])
            edge_color.append(self.REGION_COLOR_BY_TYPE[region['type']])
            line_width.append(1)
        return colors, face_color, edge_color, line_width

    def get_road_style_factory_by_name(self, name: str):
        return self.road_style_factory_dict[name]

    def get_building_style_factory_by_name(self, name: str):
        return self.building_style_factory_dict[name]

    def get_region_style_factory_by_name(self, name: str):
        return self.region_style_factory_dict[name]

    def set_current_road_style_name(self, name: str):

        assert name in self.road_style_factory_dict
        self.current_road_style_name = name

    def set_current_building_style_name(self, name: str):
        assert name in self.building_style_factory_dict
        self.current_building_style_name = name

    def set_current_region_style_name(self, name: str):
        assert name in self.region_style_factory_dict
        self.current_region_style_name = name

    def get_current_road_style_factory(self):
        return self.road_style_factory_dict[self.current_road_style_name]

    def get_current_building_style_factory(self):
        return self.building_style_factory_dict[self.current_building_style_name]

    def get_current_region_style_factory(self):
        return self.region_style_factory_dict[self.current_region_style_name]

    def show_imgui_road_color_picker(self):
        any_changed = False
        imgui.text('ROAD_COLOR_BY_LEVEL:')
        for key in self.ROAD_COLOR_BY_LEVEL:
            cs = self.ROAD_COLOR_BY_LEVEL[key]
            changed, cs = imgui.color_edit3(str(key), cs[0],cs[1],cs[2])
            any_changed |= changed
            if changed:
                self.ROAD_COLOR_BY_LEVEL[key] = cs
        return any_changed

class StyleManager:
    instance: 'StyleManager' = None

    def __init__(self):
        assert StyleManager.instance is None
        StyleManager.instance = self

        self.display_style = PlotStyle()
        self.env_style = PlotStyle()


style_manager = StyleManager()
