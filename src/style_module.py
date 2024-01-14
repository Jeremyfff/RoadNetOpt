import os.path
import pickle

import imgui
from utils import io_utils
from utils import RoadLevel, RoadState
from utils import BuildingMovableType, BuildingStyle, BuildingQuality
from utils import RegionAccessibleType


class StyleScheme:
    """风格方案"""
    def __init__(self, name):
        self.name = name
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

        self.road_style_options = list(self.road_style_factory_dict.keys())
        self.current_road_style_option = 0
        self.building_style_options = list(self.building_style_factory_dict.keys())
        self.current_building_style_option = 0
        self.region_style_options = list(self.region_style_factory_dict.keys())
        self.current_region_style_option = 0

        self.default_style_path = rf'../config/styles/{self.name}.style'
        if os.path.exists(self.default_style_path):
            self.load_from_file(self.default_style_path)

    def save_to_file(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'wb') as file:
            pickle.dump(self, file)
        print(f'[{self.name}] style saved to {file_path}')

    def load_from_file(self, file_path):
        with open(file_path, 'rb') as file:
            loaded_StyleScheme: 'StyleScheme' = pickle.load(file)
        print(f'[{self.name}] loading style from {file_path}')
        self.ROAD_COLOR_BY_LEVEL = loaded_StyleScheme.ROAD_COLOR_BY_LEVEL
        self.ROAD_WIDTH_BY_LEVEL = loaded_StyleScheme.ROAD_WIDTH_BY_LEVEL
        self.ROAD_COLOR_BY_STATE = loaded_StyleScheme.ROAD_COLOR_BY_STATE
        self.ROAD_WIDTH_BY_STATE = loaded_StyleScheme.ROAD_WIDTH_BY_STATE
        self.BUILDING_COLOR_BY_MOVABLE_TYPE = loaded_StyleScheme.BUILDING_COLOR_BY_MOVABLE_TYPE
        self.BUILDING_COLOR_BY_STYLE = loaded_StyleScheme.BUILDING_COLOR_BY_STYLE
        self.BUILDING_COLOR_BY_QUALITY = loaded_StyleScheme.BUILDING_COLOR_BY_QUALITY
        self.REGION_COLOR_BY_ACCESSIBLE = loaded_StyleScheme.REGION_COLOR_BY_ACCESSIBLE
        self.REGION_COLOR_BY_TYPE = loaded_StyleScheme.REGION_COLOR_BY_TYPE

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
            line_width.append(0)
        return colors, face_color, edge_color, line_width

    def building_style_style_factory(self, buildings):
        colors, face_color, edge_color, line_width = [], [], [], []
        for uid, building in buildings.iterrows():
            colors.append(self.BUILDING_COLOR_BY_STYLE[building['style']])
            face_color.append(self.BUILDING_COLOR_BY_STYLE[building['style']])
            edge_color.append(self.BUILDING_COLOR_BY_STYLE[building['style']])
            line_width.append(0)
        return colors, face_color, edge_color, line_width

    def building_quality_style_factory(self, buildings):
        colors, face_color, edge_color, line_width = [], [], [], []
        for uid, building in buildings.iterrows():
            colors.append(self.BUILDING_COLOR_BY_QUALITY[building['quality']])
            face_color.append(self.BUILDING_COLOR_BY_QUALITY[building['quality']])
            edge_color.append(self.BUILDING_COLOR_BY_QUALITY[building['quality']])
            line_width.append(1)
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

    def get_road_style_factory_by_idx(self, i):
        name = self.road_style_options[i]
        return self.get_road_style_factory_by_name(name)

    def get_building_style_factory_by_idx(self, i):
        name = self.building_style_options[i]
        return self.get_building_style_factory_by_name(name)

    def get_region_style_factory_by_idx(self, i):
        name = self.region_style_options[i]
        return self.get_region_style_factory_by_name(name)

    def get_current_road_style_factory_idx(self) -> int:
        return self.current_road_style_option

    def get_current_road_style_factory_name(self) -> str:
        return self.road_style_options[self.current_road_style_option]

    def get_current_building_style_factory_idx(self) -> int:
        return self.current_building_style_option

    def get_current_building_style_factory_name(self) -> str:
        return self.building_style_options[self.current_building_style_option]

    def get_current_region_style_factory_idx(self) -> int:
        return self.current_region_style_option

    def get_current_region_style_factory_name(self) -> str:
        return self.region_style_options[self.current_region_style_option]

    def get_current_road_style_factory(self):
        return self.road_style_factory_dict[self.get_current_road_style_factory_name()]

    def get_current_building_style_factory(self):
        return self.building_style_factory_dict[self.get_current_building_style_factory_name()]

    def get_current_region_style_factory(self):
        return self.region_style_factory_dict[self.get_current_region_style_factory_name()]

    def set_current_road_style_idx(self, idx: int):
        self.current_road_style_option = idx

    def set_current_building_style_idx(self, idx: int):
        self.current_building_style_option = idx

    def set_current_region_style_idx(self, idx: int):
        self.current_region_style_option = idx

    @staticmethod
    def _imgui_color_picker_template(_name, _dict):
        any_changed = False
        expanded, visible = imgui.collapsing_header(_name)
        if expanded:
            for key in _dict:
                cs = _dict[key]
                changed, cs = imgui.color_edit3(str(key), cs[0], cs[1], cs[2])
                any_changed |= changed
                if changed:
                    _dict[key] = cs
        return any_changed

    @staticmethod
    def _imgui_value_input_template(_name, _dict):
        any_changed = False
        expanded, visible = imgui.collapsing_header(_name)
        if expanded:
            for key in _dict:
                cs = _dict[key]
                changed, cs = imgui.input_float(str(key), cs)
                any_changed |= changed
                if changed:
                    _dict[key] = cs
        return any_changed

    def show_imgui_road_style_by_level_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('ROAD_COLOR_BY_LEVEL', self.ROAD_COLOR_BY_LEVEL)
        any_changed |= StyleScheme._imgui_value_input_template('ROAD_WIDTH_BY_LEVEL', self.ROAD_WIDTH_BY_LEVEL)
        return any_changed

    def show_imgui_road_style_by_state_picker(self):
        any_changed = False

        any_changed |= StyleScheme._imgui_color_picker_template('ROAD_COLOR_BY_STATE', self.ROAD_COLOR_BY_STATE)
        any_changed |= StyleScheme._imgui_value_input_template('ROAD_WIDTH_BY_STATE', self.ROAD_WIDTH_BY_STATE)
        return any_changed

    def show_imgui_building_style_by_movable_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('BUILDING_COLOR_BY_MOVABLE_TYPE', self.BUILDING_COLOR_BY_MOVABLE_TYPE)
        return any_changed

    def show_imgui_building_style_by_style_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('BUILDING_COLOR_BY_STYLE',
                                                                self.BUILDING_COLOR_BY_STYLE)
        return any_changed

    def show_imgui_building_style_by_quality_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('BUILDING_COLOR_BY_QUALITY',
                                                                self.BUILDING_COLOR_BY_QUALITY)
        return any_changed

    def show_imgui_region_style_by_accessible_picker(self):

        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('REGION_COLOR_BY_ACCESSIBLE',
                                                                self.REGION_COLOR_BY_ACCESSIBLE)
        return any_changed

    def show_imgui_region_style_by_type_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('REGION_COLOR_BY_TYPE',
                                                                self.REGION_COLOR_BY_TYPE)
        return any_changed

    def show_imgui_style_editor(self, road_style_change_callback, building_style_change_callback,
                                region_style_change_callback):
        road_style_changed = False
        building_style_changed = False
        region_style_changed = False
        expanded, visible = imgui.collapsing_header(f'{self.name} 样式方案',flags= imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            if imgui.tree_node('basic settings', imgui.TREE_NODE_DEFAULT_OPEN):
                changed, self.current_road_style_option = imgui.combo('road display:',
                                                                      self.current_road_style_option,
                                                                      self.road_style_options)
                road_style_changed |= changed

                changed, self.current_building_style_option = imgui.combo('building display:',
                                                                          self.current_building_style_option,
                                                                          self.building_style_options)
                building_style_changed |= changed

                changed, self.current_region_style_option = imgui.combo('region display:',
                                                                        self.current_region_style_option,
                                                                        self.region_style_options)
                region_style_changed |= changed

                imgui.tree_pop()
            if imgui.tree_node('advanced settings'):
                disable_color = (0,0,0,0.2)
                if self.get_current_road_style_factory_name() == 'level':
                    road_style_changed |= self.show_imgui_road_style_by_level_picker()
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_road_style_by_state_picker()
                    imgui.pop_style_color()
                elif self.get_current_road_style_factory_name() == 'state':
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_road_style_by_level_picker()
                    imgui.pop_style_color()
                    road_style_changed |= self.show_imgui_road_style_by_state_picker()

                if self.get_current_building_style_factory_name() == 'movable':
                    building_style_changed |= self.show_imgui_building_style_by_movable_picker()
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_building_style_by_style_picker()
                    self.show_imgui_building_style_by_quality_picker()
                    imgui.pop_style_color()
                elif self.get_current_region_style_factory_name() == 'style':
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_building_style_by_movable_picker()
                    imgui.pop_style_color()
                    building_style_changed |= self.show_imgui_building_style_by_style_picker()
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_building_style_by_quality_picker()
                    imgui.pop_style_color()
                elif self.get_current_building_style_factory_name() == 'quality':
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_building_style_by_movable_picker()
                    self.show_imgui_building_style_by_style_picker()
                    imgui.pop_style_color()
                    building_style_changed |= self.show_imgui_building_style_by_quality_picker()

                if self.get_current_region_style_factory_name() == 'accessible':
                    region_style_changed |= self.show_imgui_region_style_by_accessible_picker()
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_region_style_by_type_picker()
                    imgui.pop_style_color()
                elif self.get_current_region_style_factory_name() == 'region_type':
                    imgui.push_style_color(imgui.COLOR_HEADER, *disable_color)
                    self.show_imgui_region_style_by_accessible_picker()
                    imgui.pop_style_color()
                    region_style_changed |= self.show_imgui_region_style_by_type_picker()
                if imgui.button('保存为默认配置'):
                    self.save_to_file(self.default_style_path)
                if imgui.button('从磁盘加载配置'):
                    path = io_utils.open_file_window(filetypes=[('Style Files', '.style')])
                    if path is not None and path != '':
                        self.load_from_file(path)
                if imgui.button('保存配置'):
                    path = io_utils.save_file_window(defaultextension='.style',
                                              filetypes=[('Style Files', '.style')])
                    if path is not None and path != '':
                        self.save_to_file(path)
                imgui.tree_pop()



        if road_style_changed and road_style_change_callback:
            road_style_change_callback()
        if building_style_changed and building_style_change_callback:
            building_style_change_callback()
        if region_style_changed and region_style_change_callback:
            region_style_change_callback()


class StyleManager:
    instance: 'StyleManager' = None

    def __init__(self):
        assert StyleManager.instance is None
        StyleManager.instance = self

        self.display_style = StyleScheme('DISPLAY')
        self.env_style = StyleScheme('ENV')


style_manager = StyleManager()
