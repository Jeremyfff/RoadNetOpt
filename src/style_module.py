import os.path
import pickle

import imgui
import numpy as np

from utils import io_utils, common_utils
from utils import RoadLevel, RoadState
from utils import BuildingMovableType, BuildingStyle, BuildingQuality
from utils import RegionAccessibleType, RegionType
from utils import INFO_VERSION


class StyleScheme:
    """风格方案"""

    def __init__(self, name):
        self.version = INFO_VERSION
        self.name = name
        self.ROAD_COLOR_BY_LEVEL = {
            RoadLevel.TRUNK: (0, 0, 0, 1),
            RoadLevel.PRIMARY: (0.2, 0.2, 0.2, 1),
            RoadLevel.SECONDARY: (0.3, 0.3, 0.3, 1),
            RoadLevel.TERTIARY: (0.4, 0.4, 0.4, 1),
            RoadLevel.FOOTWAY: (0.6, 0.6, 0.6, 1),
            RoadLevel.UNDEFINED: (0, 0, 0, 1),
        }
        self.ROAD_WIDTH_BY_LEVEL = {
            RoadLevel.TRUNK: 5,
            RoadLevel.PRIMARY: 4,
            RoadLevel.SECONDARY: 4,
            RoadLevel.TERTIARY: 3,
            RoadLevel.FOOTWAY: 2,
            RoadLevel.UNDEFINED: 1,
        }

        self.ROAD_COLOR_BY_STATE = {
            RoadState.RAW: (0, 0, 0, 1),
            RoadState.OPTIMIZED: (0.2, 0.2, 0.2, 1),
            RoadState.OPTIMIZING: (0.4, 0.4, 0.4, 1),
        }
        self.ROAD_WIDTH_BY_STATE = {
            RoadState.RAW: 3,
            RoadState.OPTIMIZED: 3,
            RoadState.OPTIMIZING: 5,
        }

        self.BUILDING_COLOR_BY_MOVABLE_TYPE = {
            BuildingMovableType.NONDEMOLISHABLE: (0, 0, 0, 1),
            BuildingMovableType.FLEXABLE: (0.2, 0.2, 0.2, 1),
            BuildingMovableType.DEMOLISHABLE: (0.4, 0.4, 0.4, 1),
            BuildingMovableType.UNDEFINED: (0.6, 0.6, 0.6, 1)
        }
        self.BUILDING_COLOR_BY_STYLE = {
            BuildingStyle.HERITAGE: (0, 0, 0, 1),
            BuildingStyle.HISTORICAL: (0.2, 0.2, 0.2, 1),
            BuildingStyle.TRADITIONAL: (0.4, 0.4, 0.4, 1),
            BuildingStyle.NORMAL: (0.6, 0.6, 0.6, 1),
            BuildingStyle.UNDEFINED: (0.8, 0.8, 0.8, 1),
        }
        self.BUILDING_COLOR_BY_QUALITY = {
            BuildingQuality.GOOD: (0, 0, 0, 1),
            BuildingQuality.FAIR: (0.2, 0.2, 0.2, 1),
            BuildingQuality.POOR: (0.4, 0.4, 0.4, 1),
            BuildingQuality.UNDEFINED: (0.6, 0.6, 0.6, 1)
        }

        self.REGION_COLOR_BY_ACCESSIBLE = {
            RegionAccessibleType.ACCESSIBLE: (0, 0, 0, 0.3),
            RegionAccessibleType.RESTRICTED: (0.2, 0.2, 0.2, 0.3),
            RegionAccessibleType.INACCESSIBLE: (0.4, 0.4, 0.4, 0.3),
            RegionAccessibleType.UNDEFINED: (0.6, 0.6, 0.6, 0.3)
        }
        self.REGION_COLOR_BY_TYPE = {
            RegionType.ARTIFICIAL: (0, 0, 0, 0.3),
            RegionType.WATER: (0.2, 0.2, 0.2, 0.3),
            RegionType.BOUNDARY: (0.4, 0.4, 0.4, 0.3),
            RegionType.UNDEFINED: (0.6, 0.6, 0.6, 0.3)
        }

        self.NODE_COLOR = {'DEFAULT': (0, 0, 0, 1)}
        self.NODE_SIZE = {'DEFAULT': 1.0}
        self.HIGHLIGHTED_ROAD_COLOR = {'DEFAULT': (1, 1, 1, 1)}
        self.HIGHLIGHTED_ROAD_WIDTH_ADD = {'DEFAULT': 1.0}
        self.HIGHLIGHTED_NODE_COLOR = {'DEFAULT': (1, 1, 1, 1)}
        self.HIGHLIGHTED_NODE_WIDTH_ADD = {'DEFAULT': 1.0}

        self.DEFAULT_ROAD_STYLE_OPTION = 0
        self.DEFAULT_BUILDING_STYLE_OPTION = 0
        self.DEFAULT_REGION_STYLE_OPTION = 0
        # style factory dict {name: factory}
        self.road_style_factory_dict = {'level': self.road_level_style_factory,
                                        'state': self.road_state_style_factory}

        self.building_style_factory_dict = {'movable': self.building_movable_style_factory,
                                            'style': self.building_style_style_factory,
                                            'quality': self.building_quality_style_factory}

        self.region_style_factory_dict = {'accessible': self.region_accessible_style_factory,
                                          'region_type': self.region_type_style_factory}

        self.road_style_options = list(self.road_style_factory_dict.keys())
        self.current_road_style_option = self.DEFAULT_ROAD_STYLE_OPTION
        self.building_style_options = list(self.building_style_factory_dict.keys())
        self.current_building_style_option = self.DEFAULT_BUILDING_STYLE_OPTION
        self.region_style_options = list(self.region_style_factory_dict.keys())
        self.current_region_style_option = self.DEFAULT_REGION_STYLE_OPTION

        self.DEFAULT_STYLE_PATH = rf'../config/styles/{self.name}.style'
        if os.path.exists(self.DEFAULT_STYLE_PATH):
            self.load_from_file(self.DEFAULT_STYLE_PATH)

    def save_to_file(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'wb') as file:
            pickle.dump(self, file)
        file_name, file_extension = os.path.splitext(os.path.basename(file_path))
        self.name = file_name
        print(f'[{self.name}] style saved to {file_path}')

    def load_from_file(self, file_path):
        with open(file_path, 'rb') as file:
            loaded_StyleScheme: 'StyleScheme' = pickle.load(file)
        if not loaded_StyleScheme.version == self.version:
            print(f'样式文件版本不匹配')
            return
        print(f'loading style from {file_path}')
        file_name, file_extension = os.path.splitext(os.path.basename(file_path))
        self.name = file_name
        attributes = [
            "ROAD_COLOR_BY_LEVEL",
            "ROAD_WIDTH_BY_LEVEL",
            "ROAD_COLOR_BY_STATE",
            "ROAD_WIDTH_BY_STATE",
            "BUILDING_COLOR_BY_MOVABLE_TYPE",
            "BUILDING_COLOR_BY_STYLE",
            "BUILDING_COLOR_BY_QUALITY",
            "REGION_COLOR_BY_ACCESSIBLE",
            "REGION_COLOR_BY_TYPE",
            "NODE_COLOR",
            "NODE_SIZE",
            "HIGHLIGHTED_ROAD_COLOR",
            "HIGHLIGHTED_ROAD_WIDTH_ADD",
            "HIGHLIGHTED_NODE_COLOR",
            "HIGHLIGHTED_NODE_WIDTH_ADD",
            "DEFAULT_ROAD_STYLE_OPTION",
            "DEFAULT_BUILDING_STYLE_OPTION",
            "DEFAULT_REGION_STYLE_OPTION"
        ]
        for attr in attributes:
            try:
                exec(f"self.{attr} = loaded_StyleScheme.{attr}")
            except Exception as e:
                print(f"An error occurred while loading style scheme: {e}")
        self.current_road_style_option = self.DEFAULT_ROAD_STYLE_OPTION
        self.current_building_style_option = self.DEFAULT_BUILDING_STYLE_OPTION
        self.current_region_style_option = self.DEFAULT_BUILDING_STYLE_OPTION

    def road_level_style_factory(self, roads):
        colors = np.array(roads['level'].map(self.ROAD_COLOR_BY_LEVEL).values.tolist())
        width = np.array(roads['level'].map(self.ROAD_WIDTH_BY_LEVEL).values.tolist())
        return colors, width

    def road_state_style_factory(self, roads):
        colors = np.array(roads['state'].map(self.ROAD_COLOR_BY_STATE).values.tolist())
        width = np.array(roads['state'].map(self.ROAD_WIDTH_BY_STATE).values.tolist())
        return colors, width

    def road_idx_style_factory(self, roads):
        """将road idx 编码为uint32， 并转换为4个uint8，
        其中最后一个透明通道需要始终保持为不透明状态，因此实际只有三个uint8的空间可以使用
        为了增加颜色编码的识别度，使用以3为步长的序号编码，
        因此最大支持的道路数量为uint24的最大表示数字 16_777_216 / 3"""
        _ = self
        if roads is None: return
        num = len(roads)
        assert num < 16_777_216 / 3, '达到uint24 能表达的道路数量上限'
        idx_uint32 = np.arange(num, dtype=np.uint32).reshape(num, 1) * 3
        rgb_uint8 = idx_uint32.view(np.uint8).reshape(num, 4)[:, :3]
        rgb_float32 = rgb_uint8.astype(np.float32) / 256.0
        alpha_float32 = np.ones((num, 1), dtype=np.float32)
        colors = np.concatenate((rgb_float32, alpha_float32), axis=1)

        curr_factory_name = self.get_current_road_style_factory_name()
        if curr_factory_name == 'level':
            width = np.array(roads['level'].map(self.ROAD_WIDTH_BY_LEVEL).values.tolist())
        elif curr_factory_name == 'state':
            width = np.array(roads['state'].map(self.ROAD_WIDTH_BY_STATE).values.tolist())
        else:
            raise Exception('遇到未知的style_factory_name')
        return colors, width

    def road_highlight_style_factory(self, roads):
        _ = self
        if roads is None: return
        num = len(roads)
        colors = np.full((num, 4), self.HIGHLIGHTED_ROAD_COLOR['DEFAULT'])
        curr_factory_name = self.get_current_road_style_factory_name()
        if curr_factory_name == 'level':
            width = np.array(roads['level'].map(self.ROAD_WIDTH_BY_LEVEL).values.tolist())
            width += self.HIGHLIGHTED_ROAD_WIDTH_ADD['DEFAULT']
        elif curr_factory_name == 'state':
            width = np.array(roads['state'].map(self.ROAD_WIDTH_BY_STATE).values.tolist())
            width += self.HIGHLIGHTED_ROAD_WIDTH_ADD['DEFAULT']
        else:
            raise Exception('遇到未知的style_factory_name')
        return colors, width

    def node_style_factory(self, nodes):
        _ = self
        if nodes is None: return
        num = len(nodes)
        width = np.full(num, self.NODE_SIZE['DEFAULT'])
        colors = np.full((num, 4), self.NODE_COLOR['DEFAULT'])
        return colors, width

    def node_idx_style_factory(self, nodes):
        """将node idx 编码为uint32， 并转换为4个uint8，
        其中最后一个透明通道需要始终保持为不透明状态，因此实际只有三个uint8的空间可以使用
        为了增加颜色编码的识别度，使用以3为步长的序号编码，
        因此最大支持的道路数量为uint24的最大表示数字 16_777_216 / 3"""
        _ = self
        if nodes is None: return
        num = len(nodes)
        assert num < 16_777_216 / 3, '达到uint24 能表达的数量上限'
        idx_uint32 = np.arange(num, dtype=np.uint32).reshape(num, 1) * 3
        rgb_uint8 = idx_uint32.view(np.uint8).reshape(num, 4)[:, :3]
        rgb_float32 = rgb_uint8.astype(np.float32) / 256.0
        alpha_float32 = np.ones((num, 1), dtype=np.float32)
        colors = np.concatenate((rgb_float32, alpha_float32), axis=1)
        width = np.full(num, self.NODE_SIZE['DEFAULT'])
        return colors, width

    def node_highlight_style_factory(self, nodes):
        _ = self
        if nodes is None: return
        num = len(nodes)
        colors = np.full((num, 4), self.HIGHLIGHTED_NODE_COLOR['DEFAULT'])
        width = np.full(num, self.NODE_SIZE['DEFAULT'] + self.HIGHLIGHTED_NODE_WIDTH_ADD['DEFAULT'])
        return colors, width

    def building_movable_style_factory(self, buildings):
        colors = np.array(buildings['movable'].map(self.BUILDING_COLOR_BY_MOVABLE_TYPE).values.tolist())
        face_color = colors
        edge_color = colors
        return colors, face_color, edge_color

    def building_style_style_factory(self, buildings):
        colors = np.array(buildings['style'].map(self.BUILDING_COLOR_BY_STYLE).values.tolist())
        face_color = colors
        edge_color = colors
        return colors, face_color, edge_color

    def building_quality_style_factory(self, buildings):
        colors = np.array(buildings['quality'].map(self.BUILDING_COLOR_BY_STYLE).values.tolist())
        face_color = colors
        edge_color = colors
        return colors, face_color, edge_color

    def region_accessible_style_factory(self, regions):
        colors = np.array(regions['accessible'].map(self.REGION_COLOR_BY_ACCESSIBLE).values.tolist())
        face_color = colors
        edge_color = colors
        return colors, face_color, edge_color

    def region_type_style_factory(self, regions):
        colors = np.array(regions['region_type'].map(self.REGION_COLOR_BY_TYPE).values.tolist())
        face_color = colors
        edge_color = colors
        return colors, face_color, edge_color

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
            imgui.push_id(_name)
            for key in _dict:
                cs = _dict[key]
                if len(cs) == 3:
                    changed, cs = imgui.color_edit3(str(key), cs[0], cs[1], cs[2])
                elif len(cs) == 4:
                    changed, cs = imgui.color_edit4(str(key), cs[0], cs[1], cs[2], cs[3])
                else:
                    raise Exception('不支持的色彩格式')
                any_changed |= changed
                if changed:
                    _dict[key] = cs
            imgui.pop_id()
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

    def show_imgui_highlighted_road_style_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('HIGHLIGHTED_ROAD_COLOR', self.HIGHLIGHTED_ROAD_COLOR)
        any_changed |= StyleScheme._imgui_value_input_template('HIGHLIGHTED_ROAD_WIDTH_ADD',
                                                               self.HIGHLIGHTED_ROAD_WIDTH_ADD)
        return any_changed

    def show_imgui_highlighted_node_style_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('HIGHLIGHTED_NODE_COLOR', self.HIGHLIGHTED_NODE_COLOR)
        any_changed |= StyleScheme._imgui_value_input_template('HIGHLIGHTED_NODE_WIDTH_ADD',
                                                               self.HIGHLIGHTED_NODE_WIDTH_ADD)
        return any_changed

    def show_imgui_building_style_by_movable_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('BUILDING_COLOR_BY_MOVABLE_TYPE',
                                                                self.BUILDING_COLOR_BY_MOVABLE_TYPE)
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

    def show_imgui_node_style_picker(self):
        any_changed = False
        any_changed |= StyleScheme._imgui_color_picker_template('NODE_COLOR', self.NODE_COLOR)
        any_changed |= StyleScheme._imgui_value_input_template('NODE_SIZE', self.NODE_SIZE)
        return any_changed

    def show_imgui_style_editor(self, road_style_change_callback, building_style_change_callback,
                                region_style_change_callback, node_style_change_callback,
                                highlight_style_change_callback):
        road_style_changed = False
        building_style_changed = False
        region_style_changed = False
        node_style_changed = False
        highlight_style_changed = False

        expanded, visible = imgui.collapsing_header(f'样式方案 ({self.name})', flags=imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            if imgui.tree_node('BASIC SETTINGS', imgui.TREE_NODE_DEFAULT_OPEN):
                changed, self.current_road_style_option = \
                    imgui.combo('Road Display:', self.current_road_style_option, self.road_style_options)
                road_style_changed |= changed
                if self.current_road_style_option != self.DEFAULT_ROAD_STYLE_OPTION:
                    imgui.same_line()
                    if imgui.button('Set as default'):
                        self.DEFAULT_ROAD_STYLE_OPTION = self.current_road_style_option
                changed, self.current_building_style_option = \
                    imgui.combo('Building Display:', self.current_building_style_option, self.building_style_options)
                building_style_changed |= changed
                if self.current_building_style_option != self.DEFAULT_BUILDING_STYLE_OPTION:
                    imgui.same_line()
                    if imgui.button('Set as default'):
                        self.DEFAULT_BUILDING_STYLE_OPTION = self.current_building_style_option
                changed, self.current_region_style_option = \
                    imgui.combo('Region Display:', self.current_region_style_option, self.region_style_options)
                region_style_changed |= changed
                if self.current_region_style_option != self.DEFAULT_REGION_STYLE_OPTION:
                    imgui.same_line()
                    if imgui.button('Set as default'):
                        self.DEFAULT_REGION_STYLE_OPTION = self.current_region_style_option
                imgui.tree_pop()
            if imgui.tree_node('ADVANCED SETTINGS'):
                disable_color = (0, 0, 0, 0.2)
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
                elif self.get_current_building_style_factory_name() == 'style':
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
                highlight_style_changed |= self.show_imgui_highlighted_road_style_picker()
                highlight_style_changed |= self.show_imgui_highlighted_node_style_picker()
                node_style_changed |= self.show_imgui_node_style_picker()
                if imgui.button('保存为默认配置'):
                    self.save_to_file(self.DEFAULT_STYLE_PATH)
                if imgui.button('从磁盘加载配置'):
                    path = io_utils.open_file_window(filetypes=[('Style Files', '.style')])
                    if path is not None and path != '':
                        self.load_from_file(path)
                if imgui.button('另存为配置'):
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
        if node_style_changed and node_style_change_callback:
            node_style_change_callback()
        if highlight_style_changed and highlight_style_change_callback:
            highlight_style_change_callback()


class StyleManager:
    instance: 'StyleManager' = None
    I: 'StyleManager' = None  # 缩写

    def __init__(self):
        assert StyleManager.instance is None
        StyleManager.instance = self
        StyleManager.I = self

        self.display_style = StyleScheme('DISPLAY')
        self.env_style = StyleScheme('ENV')

    @property
    def dis(self):
        return self.display_style

    @property
    def env(self):
        return self.env_style


style_manager = StyleManager()
