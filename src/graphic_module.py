import logging
import matplotlib
import moderngl
import numpy as np
from OpenGL.GL import *
from PIL import Image
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
from datetime import datetime
from moderngl_window.opengl.vao import VAO
import imgui
import geopandas as gpd
import torch
from typing import *
from gui import global_var as g
from geo import Road, Building, Region
from style_module import StyleManager as sm
from utils import RoadCluster, BuildingCluster, RegionCluster
from utils import common_utils
from utils.common_utils import timer
from utils import graphic_uitls
from gui.icon_module import IconManager, Spinner

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class SimpleTexture:
    def __init__(self, name, width, height, channel=4):
        self.name = name
        self.width, self.height, self.channel = width, height, channel
        self.exposed = True
        self.ctx = g.mCtx
        self.texture = self.ctx.texture((width, height), channel, None)
        self.x_lim = None
        self.y_lim = None
        g.mModernglWindowRenderer.register_texture(self.texture)

    @property
    def texture_id(self):
        return self.texture.glo

    def bilt_data(self, data):
        height, width, channel = data.shape
        if height != self.height or width != self.width or channel != self.channel:
            g.mModernglWindowRenderer.remove_texture(self.texture)
            self.texture = g.mCtx.texture((width, height), channel, data.tobytes())
            self.height, self.width, self.channel = height, width, channel
            g.mModernglWindowRenderer.register_texture(self.texture)
        else:
            self.texture.write(data.tobytes())


class FrameBufferTexture:
    """
    使用moderngl的 framebuffer作为渲染画布的高级包装texture对象
    此类为基类， 实现了基础属性的获取与修改，支持改变texture的尺寸并自动注册和销毁
    要对该texture进行修改，需要继承该类的render方法并对其进行自定义修改

    """

    def __init__(self, name, width, height, channel=4):
        self.name = name
        self.width, self.height, self.channel = width, height, channel
        self.exposed = True
        self.x_lim = None  # 世界坐标
        self.y_lim = None  # 世界坐标

        self.ctx = g.mCtx
        self.fbo = self.ctx.framebuffer(
            color_attachments=self.ctx.texture((width, height), 4)
        )
        g.mModernglWindowRenderer.register_texture(self.fbo.color_attachments[0])

    @property
    def texture(self):
        return self.fbo.color_attachments[0]

    @property
    def texture_id(self):
        return self.texture.glo

    def update_size(self, width, height):
        g.mModernglWindowRenderer.remove_texture(self.fbo.color_attachments[0])
        self.width, self.height = width, height

        self.fbo = self.ctx.framebuffer(
            color_attachments=self.ctx.texture((width, height), 4)
        )
        g.mModernglWindowRenderer.register_texture(self.fbo.color_attachments[0])
        print(f'texture size updated to {self.width, self.height}, id = {self.fbo.color_attachments[0].glo}')

    def render(self, **kwargs):
        pass


class MainFrameBufferTexture(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)

        # clusters
        self.road_cluster = RoadCluster()
        self.building_cluster = BuildingCluster()
        self.region_cluster = RegionCluster()

        # params
        self.enable_render_roads = True
        self.enable_render_buildings = False
        self.enable_render_regions = False
        self.enable_render_nodes = False
        self.enable_mouse_pointer = True  # 是否显示鼠标光标定位十字

        self._any_change = False  # 是否有任何变化
        self._lazy_update = True  # 只有当有变化发生时才会渲染

        self._need_check_roads = True
        self._need_check_buildings = True
        self._need_check_regions = True
        self._need_check_nodes = True
        self._need_check_highlighted_roads = True
        self._need_check_highlighted_nodes = True
        self._need_check_road_idx = True
        self._need_check_node_idx = True

        # caches
        self.cached_road_uid = None
        self.cached_building_uid = None
        self.cached_region_uid = None

        # vertex array objects, buffer and programs
        _rsf = sm.I.dis.get_current_road_style_factory()
        _bsf = sm.I.dis.get_current_building_style_factory()
        _resf = sm.I.dis.get_current_region_style_factory()
        _nsf = sm.I.dis.node_style_factory
        _rhsf = sm.I.dis.road_highlight_style_factory
        _nhsf = sm.I.dis.node_highlight_style_factory

        self.road_gl = graphic_uitls.RoadGL('road', _rsf)
        self.building_gl = graphic_uitls.BuildingGL('building', _bsf)
        self.region_gl = graphic_uitls.RegionGL('region', _resf)
        self.node_gl = graphic_uitls.NodeGL('node', _nsf)
        self.highlighted_road_gl = graphic_uitls.RoadGL('highlighted_road', _rhsf)
        self.highlighted_node_gl = graphic_uitls.NodeGL('highlighted_node', _nhsf)
        self.pointer_gl = graphic_uitls.PointerGL()
        self.rect_gl = graphic_uitls.RectGL('drag_selection')

        self._road_idx_texture = RoadIdxFrameBufferTexture('road_idx', self.width, self.height)
        self._node_idx_texture = NodeIdxFrameBufferTexture('road_idx', self.width, self.height)

        # imgui draw list
        self._close_node_debug_circles: list[graphic_uitls.ImguiCircleWorldSpace] = []
        self._close_node_debug_texts: list[graphic_uitls.ImguiTextWorldSpace] = []
        self._intersection_debug_circles: list[graphic_uitls.ImguiCircleWorldSpace] = []
        self._intersection_debug_texts: list[graphic_uitls.ImguiTextWorldSpace] = []

        self._drag_selection_start_pos = None
        self._cached_road_or_node_idx_img_arr = None

    def show_imgui_display_editor(self):
        road_changed = False
        building_changed = False
        region_changed = False
        # roads
        IconManager.imgui_icon('road-fill')
        imgui.same_line()
        clicked, self.enable_render_roads = imgui.checkbox('render roads', True)
        if clicked:
            imgui.open_popup('warning')

        if imgui.begin_popup_modal('warning',
                                   flags=imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_ALWAYS_AUTO_RESIZE).opened:

            size = imgui.get_window_size()
            imgui.set_window_position(g.mWindowSize[0] / 2 - size.x / 2, g.mWindowSize[1] / 2 - size.y / 2)
            imgui.text('不能关闭道路的显示')
            if imgui.button('知道了', width=size.x - 16, height=22):
                imgui.close_current_popup()
            imgui.end_popup()
        if self.enable_render_roads:
            imgui.indent()
            road_changed |= self.road_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        # buildings
        IconManager.imgui_icon('building-fill')
        imgui.same_line()
        clicked, self.enable_render_buildings = imgui.checkbox('render buildings', self.enable_render_buildings)
        if clicked:
            self._any_change = True
        if self.enable_render_buildings:
            imgui.indent()
            building_changed |= self.building_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        # regions
        IconManager.imgui_icon('polygon')
        imgui.same_line()
        clicked, self.enable_render_regions = imgui.checkbox('render regions', self.enable_render_regions)
        if clicked:
            self._any_change = True
        if self.enable_render_regions:
            imgui.indent()
            region_changed |= self.region_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()

        # nodes
        IconManager.imgui_icon('vector-polygon')
        imgui.same_line()
        clicked, self.enable_render_nodes = imgui.checkbox('render nodes', self.enable_render_nodes)
        if clicked:
            self._any_change = True

        if road_changed:
            self.clear_road_data()
        if building_changed:
            self.clear_building_data()
        if region_changed:
            self.clear_region_data()

    def show_imgui_main_texture_settings(self):
        changed, value = imgui.drag_float('resolution scale', 1 / g.TEXTURE_SCALE, 0.01, 0.1, 2)
        if changed:
            g.TEXTURE_SCALE = 1 / value
        clicked, state = imgui.checkbox('show pointer', self.enable_mouse_pointer)
        if clicked:
            self.enable_mouse_pointer = state

    def _check_roads(self):
        """
        检查roads是否需要更新，两种情况会导致其进行更新操作：
        1. self._need_check_roads被设置为True
        2. Road.uid 发生了变化，此处的uid为Road类的整体uid，当Road类发生任何变化都会使该值发生变化。
           当使用road cluster筛选出特定的道路进行显示时， 当未显示的road发生变化时，也会进行更新
            下述的所有check与之相同，不再赘述
        :return:
        """
        if self._need_check_roads or self.cached_road_uid != Road.uid():

            self.road_gl.set_gdf(Road.get_roads_by_cluster(self.road_cluster))
            self.road_gl.set_style_factory(sm.I.dis.get_current_road_style_factory())
            self.road_gl.update_buffer()

            if self.cached_road_uid != Road.uid():
                # 当road结构发生变化时，将相关变量设为需要检查
                self._need_check_nodes = True
                self._need_check_road_idx = True
                self._need_check_node_idx = True

            self.cached_road_uid = Road.uid()
            self._need_check_roads = False
            self._any_change = True

            return True
        else:
            return False

    def _check_buildings(self):
        if self._need_check_buildings or self.cached_building_uid != Building.uid():
            self.building_gl.set_gdf(Building.get_buildings_by_cluster(self.building_cluster))
            self.building_gl.set_style_factory(sm.I.dis.get_current_building_style_factory())
            self.building_gl.update_buffer()

            self.cached_building_uid = Building.uid()
            self._need_check_buildings = False
            self._any_change = True
            return True
        else:
            return False

    def _check_regions(self):
        if self._need_check_regions or self.cached_region_uid != Region.uid():
            self.region_gl.set_gdf(Region.get_regions_by_cluster(self.region_cluster))
            self.region_gl.set_style_factory(sm.I.dis.get_current_region_style_factory())
            self.region_gl.update_buffer()

            self.cached_region_uid = Region.uid()
            self._need_check_regions = False
            self._any_change = True
            return True
        else:
            return False

    def _check_highlighted_roads(self):
        if self._need_check_highlighted_roads:
            roads_dict = g.mSelectedRoads
            keys = roads_dict.keys()
            if len(keys) == 0:
                roads = None
            elif len(keys) == 1:
                roads = list(roads_dict.values())[0]
                roads = roads.to_frame().T
            else:
                roads = [road.to_frame().T for road in list(roads_dict.values())]
                roads = gpd.pd.concat(roads, ignore_index=False)

            self.highlighted_road_gl.set_gdf(roads)
            self.highlighted_road_gl.update_buffer()

            self._need_check_highlighted_roads = False
            self._any_change = True
            return True
        else:
            return False

    def _check_highlighted_nodes(self):
        if self._need_check_highlighted_nodes:
            nodes_dict = g.mSelectedNodes
            keys = nodes_dict.keys()
            if len(keys) == 0:
                nodes = None
            elif len(keys) == 1:
                nodes = list(nodes_dict.values())[0]
                nodes = nodes.to_frame().T
            else:
                nodes = [node.to_frame().T for node in list(nodes_dict.values())]
                nodes = gpd.pd.concat(nodes, ignore_index=False)

            self.highlighted_node_gl.set_gdf(nodes)
            self.highlighted_node_gl.update_buffer()

            self._need_check_highlighted_nodes = False
            self._any_change = True
            return True
        else:
            return False

    def _check_road_idx(self):
        if self._need_check_road_idx:
            self._road_idx_texture.road_idx_gl.set_gdf(Road.get_roads_by_cluster(self.road_cluster))
            self._road_idx_texture.road_idx_gl.update_buffer()
            self._need_check_road_idx = False
            self._any_change = True
        else:
            return False

    def _check_node_idx(self):
        if self._need_check_node_idx:
            self._node_idx_texture.node_idx_gl.set_gdf(Road.get_all_nodes())
            self._node_idx_texture.node_idx_gl.update_buffer()
            self._need_check_node_idx = False
            self._any_change = True

    def _check_nodes(self):
        if self._need_check_nodes:
            self.node_gl.set_gdf(Road.get_all_nodes())
            self.node_gl.set_style_factory(sm.I.dis.node_style_factory)
            self.node_gl.update_buffer()

            self._need_check_nodes = False
            self._any_change = True
            return True
        else:
            return False

    def _in_regions(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def _render_and_get_road_idx_uint8_img_arr(self):
        self._road_idx_texture.fbo.use()
        self._road_idx_texture.fbo.clear(1, 1, 1, 0)  # 前三个通道表示id， alpha通道表示是否有道路
        self._road_idx_texture.road_idx_gl.update_prog(self.x_lim, self.y_lim)
        self._road_idx_texture.road_idx_gl.render()
        texture = self._road_idx_texture.texture
        img_uint8 = np.frombuffer(self._road_idx_texture.fbo.color_attachments[0].read(), dtype=np.uint8).reshape(
            (texture.height, texture.width, 4))
        return img_uint8

    def _render_and_get_node_idx_uint8_img_arr(self):
        self._node_idx_texture.fbo.use()
        self._node_idx_texture.fbo.clear(1, 1, 1, 0)  # 前三个通道表示id， alpha通道表示是否有道路
        self._node_idx_texture.node_idx_gl.update_prog(self.x_lim, self.y_lim)
        self._node_idx_texture.node_idx_gl.render()
        texture = self._node_idx_texture.texture
        img_uint8 = np.frombuffer(self._node_idx_texture.fbo.color_attachments[0].read(), dtype=np.uint8).reshape(
            (texture.height, texture.width, 4))
        return img_uint8

    def get_road_or_node_idx_by_mouse_pos(self, texture_space_mouse_pos, select_roads=True) -> Union[int, None]:
        if not self._in_regions(texture_space_mouse_pos): return None
        if self.x_lim is None or self.y_lim is None: return None
        if select_roads:
            img_uint8 = self._render_and_get_road_idx_uint8_img_arr()
        else:
            img_uint8 = self._render_and_get_node_idx_uint8_img_arr()
        color_uint8 = img_uint8[texture_space_mouse_pos[1], texture_space_mouse_pos[0], :]
        if color_uint8[3] == 0: return None  # click on blank
        color_uint8 = color_uint8.copy()
        color_uint8[3] = 0
        idx_uint32 = color_uint8.view(np.uint32)
        idx_float = idx_uint32.astype(np.float32) / 3.0
        idx_int = int(np.round(idx_float)[0])
        return idx_int

    def start_drag_selection(self, texture_space_mouse_pos, select_roads=True):
        if not self._in_regions(texture_space_mouse_pos): return
        if self.x_lim is None or self.y_lim is None: return
        self._drag_selection_start_pos = texture_space_mouse_pos
        if select_roads:
            self._cached_road_or_node_idx_img_arr = self._render_and_get_road_idx_uint8_img_arr()
        else:
            self._cached_road_or_node_idx_img_arr = self._render_and_get_node_idx_uint8_img_arr()
        self._any_change = True

    def update_drag_selection(self, texture_space_mouse_pos):
        if self._drag_selection_start_pos is None or self._cached_road_or_node_idx_img_arr is None:
            return None
        x_min = min(texture_space_mouse_pos[0], self._drag_selection_start_pos[0])
        x_max = max(texture_space_mouse_pos[0], self._drag_selection_start_pos[0])
        y_min = min(texture_space_mouse_pos[1], self._drag_selection_start_pos[1])
        y_max = max(texture_space_mouse_pos[1], self._drag_selection_start_pos[1])
        img_arr_slice = self._cached_road_or_node_idx_img_arr[y_min:y_max, x_min:x_max, :].reshape(-1, 4)
        img_arr_slice = img_arr_slice[img_arr_slice[:, 3] != 0]
        arr_uint8 = np.unique(img_arr_slice, axis=0)
        arr_uint8[:, 3] = 0
        arr_uint32 = arr_uint8.view(np.uint32).flatten()
        arr_float = arr_uint32.astype(np.float32) / 3.0
        idx_list = np.round(arr_float).astype(np.int32).tolist()
        self._any_change = True
        return idx_list

    def end_drag_selection(self):
        self._drag_selection_start_pos = None
        self._cached_road_or_node_idx_img_arr = None
        self._any_change = True

    def clear_cache(self):
        self.x_lim = None
        self.y_lim = None
        self.recheck_all()

    def recheck_all(self):
        self._need_check_roads = True
        self._need_check_buildings = True
        self._need_check_regions = True
        self._need_check_nodes = True
        self._need_check_road_idx = True
        self._need_check_node_idx = True
        self._need_check_highlighted_roads = True
        self._need_check_highlighted_nodes = True

    def clear_highlight_data(self):
        self._need_check_highlighted_roads = True
        self._need_check_highlighted_nodes = True

    def clear_road_data(self):
        """适用于road的颜色、显示等发生改变时"""
        self._need_check_roads = True

    def clear_road_data_deep(self):
        """适用于road的文件结构改变时"""
        self._need_check_roads = True
        self._need_check_road_idx = True
        self._need_check_node_idx = True
        self._need_check_highlighted_roads = True
        self._need_check_highlighted_nodes = True

    def clear_building_data(self):
        self._need_check_buildings = True

    def clear_region_data(self):
        self._need_check_regions = True

    def clear_node_data(self):
        self._need_check_nodes = True

    def clear_x_y_lim(self):
        self.x_lim = None
        self.y_lim = None

    @property
    def texture_ratio(self):
        return self.width / self.height

    @property
    def world_space_width(self):
        if self.x_lim is None:
            return 0
        else:
            return self.x_lim[1] - self.x_lim[0]

    @property
    def world_space_height(self):
        if self.y_lim is None:
            return 0
        else:
            return self.y_lim[1] - self.y_lim[0]

    @property
    def mouse_pos_percent(self):
        return float(g.mMousePosInImage[0]) / self.width, float(g.mMousePosInImage[1]) / self.height

    def zoom_all(self):
        print('zoom all')
        x_lim, y_lim = self.road_gl.get_xy_lim()
        y_center = (y_lim[0] + y_lim[1]) / 2
        y_size = y_lim[1] - y_lim[0]
        y_size *= 1.05
        self.y_lim = (y_center - y_size / 2, y_center + y_size / 2)
        x_center = (x_lim[0] + x_lim[1]) / 2
        x_size = self.texture_ratio * y_size
        self.x_lim = (x_center - x_size / 2, x_center + x_size / 2)
        self._any_change = True

    def pan(self, texture_space_delta: tuple):
        if self.x_lim is None or self.y_lim is None:
            return
        x_ratio = self.world_space_width / self.width
        y_ratio = self.world_space_height / self.height
        x_delta = texture_space_delta[0] * -x_ratio
        y_delta = texture_space_delta[1] * y_ratio
        self.x_lim = (self.x_lim[0] + x_delta, self.x_lim[1] + x_delta)
        self.y_lim = (self.y_lim[0] + y_delta, self.y_lim[1] + y_delta)
        self._any_change = True

    def zoom(self, texture_space_center: tuple, percent: float):
        if self.x_lim is None or self.y_lim is None:
            return
        if percent == 0:
            return
        ts_cx = texture_space_center[0]
        ts_cy = self.height - texture_space_center[1]
        ws_cx = self.world_space_width * ts_cx / self.width + self.x_lim[0]
        ws_cy = self.world_space_height * ts_cy / self.height + self.y_lim[0]

        nx = self.x_lim[0] - ws_cx
        px = self.x_lim[1] - ws_cx
        ny = self.y_lim[0] - ws_cy
        py = self.y_lim[1] - ws_cy
        nx *= percent
        px *= percent
        ny *= percent
        py *= percent
        self.x_lim = (ws_cx + nx, ws_cx + px)
        self.y_lim = (ws_cy + ny, ws_cy + py)
        self._any_change = True

    def add_close_node_debug_circle(self, world_x, world_y, screen_radius, tuple_color, content):
        circle = graphic_uitls.ImguiCircleWorldSpace(world_x, world_y,
                                                     screen_radius, tuple_color,
                                                     g.mImageWindowDrawList, self)
        text = graphic_uitls.ImguiTextWorldSpace(world_x, world_y,
                                                 content, tuple_color,
                                                 g.mImageWindowDrawList, self)

        self._close_node_debug_circles.append(circle)
        self._close_node_debug_texts.append(text)

    def clear_close_node_debug_circles(self):
        self._close_node_debug_circles = []
        self._close_node_debug_texts = []

    def add_intersection_debug_circle(self, world_x, world_y, screen_radius, tuple_color, content):
        circle = graphic_uitls.ImguiCircleWorldSpace(world_x, world_y,
                                                     screen_radius, tuple_color,
                                                     g.mImageWindowDrawList, self)
        text = graphic_uitls.ImguiTextWorldSpace(world_x, world_y,
                                                 content, tuple_color,
                                                 g.mImageWindowDrawList, self)
        self._intersection_debug_circles.append(circle)
        self._intersection_debug_texts.append(text)

    def clear_intersection_debug_circles(self):
        self._intersection_debug_circles = []
        self._intersection_debug_texts = []

    def render(self, **kwargs):
        """被调用即进行渲染，不进行逻辑判断"""
        self.fbo.use()
        self.fbo.clear()
        if self.x_lim is None:  # 只有在x_lim被清空或第一次运行时才会获取
            self.zoom_all()
        if self.enable_render_regions:
            self.region_gl.update_prog(self.x_lim, self.y_lim)
            self.region_gl.render()
        if self.enable_render_buildings:
            self.building_gl.update_prog(self.x_lim, self.y_lim)
            self.building_gl.render()
        if self.enable_render_roads:
            self.road_gl.update_prog(self.x_lim, self.y_lim)
            self.road_gl.render()
            self.highlighted_road_gl.update_prog(self.x_lim, self.y_lim)
            self.highlighted_road_gl.render()
        if self.enable_render_nodes:
            self.node_gl.update_prog(self.x_lim, self.y_lim)
            self.node_gl.render()
            self.highlighted_node_gl.update_prog(self.x_lim, self.y_lim)
            self.highlighted_node_gl.render()
        if self.enable_mouse_pointer:
            self.pointer_gl.update_prog(offset=self.mouse_pos_percent, texture_size=self.texture.size)
            self.pointer_gl.render()
        if self._drag_selection_start_pos is not None:
            start = (float(self._drag_selection_start_pos[0]) / self.width,
                     float(self._drag_selection_start_pos[1]) / self.height)
            size = (float(g.mMousePosInImage[0] - self._drag_selection_start_pos[0]) / self.width,
                    float(g.mMousePosInImage[1] - self._drag_selection_start_pos[1]) / self.height)
            self.rect_gl.update_prog(start=start, size=size)
            self.rect_gl.render()

    def update(self, **kwargs):
        """每帧调用"""
        if len(Road.get_all_roads()) == 0:
            return
        width, height = g.mImageSize
        if width != self.width or height != self.height:
            self.update_size(width, height)
            self._road_idx_texture.update_size(width, height)
            self._node_idx_texture.update_size(width, height)
            self.clear_x_y_lim()
            self._any_change = True

        if self.enable_render_roads:
            self._check_roads()
            self._check_highlighted_roads()
            self._check_road_idx()
            self._check_node_idx()
        if self.enable_render_buildings:
            self._check_buildings()
        if self.enable_render_regions:
            self._check_regions()
        if self.enable_render_nodes:
            self._check_nodes()
            self._check_highlighted_nodes()

        if self._any_change or self.enable_mouse_pointer or not self._lazy_update:
            self.render(**kwargs)
            self._any_change = False

    def render_draw_list(self):
        if self.x_lim is None or self.y_lim is None:
            return
        if self._close_node_debug_circles:
            for circle in self._close_node_debug_circles:
                circle.draw()
        if self._close_node_debug_texts:
            for text in self._close_node_debug_texts:
                text.draw()
        if self._intersection_debug_circles:
            for circle in self._intersection_debug_circles:
                circle.draw()
        if self._intersection_debug_texts:
            for text in self._intersection_debug_texts:
                text.draw()


class RoadIdxFrameBufferTexture(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
        self.road_idx_gl = graphic_uitls.RoadGL('road_idx', sm.I.dis.road_idx_style_factory)


class NodeIdxFrameBufferTexture(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
        self.node_idx_gl = graphic_uitls.NodeGL('node_idx', sm.I.dis.node_idx_style_factory)


class AgentFrameBufferTexture(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
        self.exposed = False

        _rsf = sm.I.env.road_level_style_factory
        _bsf = sm.I.env.building_movable_style_factory
        _resf = sm.I.env.region_accessible_style_factory

        self.road_gl = graphic_uitls.RoadGL('road', _rsf)
        self.building_gl = graphic_uitls.BuildingGL('building', _bsf)
        self.region_gl = graphic_uitls.RegionGL('region', _resf)

        self.cached_road_uid = None

    def set_observation_space(self, center, size):
        self.x_lim = (center[0] - size, center[0] + size)
        self.y_lim = (center[1] - size, center[1] + size)

    def update_roads_buffer(self):
        self.road_gl.set_gdf(Road.get_all_roads())
        self.road_gl.update_buffer()
        self.cached_road_uid = Road.uid()

    def render(self):
        if self.x_lim is None or self.y_lim is None:
            return
        if self.cached_road_uid != Road.uid():
            self.update_roads_buffer()
        self.fbo.use()
        self.fbo.clear()
        self.region_gl.update_prog(self.x_lim, self.y_lim)
        self.region_gl.render()
        self.building_gl.update_prog(self.x_lim, self.y_lim)
        self.building_gl.render()
        self.road_gl.update_prog(self.x_lim, self.y_lim)
        self.road_gl.render()

    def get_last_render_img(self):
        img_uint8 = np.frombuffer(self.texture.read(), dtype=np.uint8).reshape(
            (self.texture.height, self.texture.width, 4))
        return img_uint8


class GraphicManager:
    instance: 'GraphicManager' = None

    def __init__(self):
        GraphicManager.instance = self
        self.textures = {}
        width, height = g.mWindowSize
        # self.main_texture: MainGraphTexture = MainGraphTexture('main', width - 400, height - 200)
        self.main_texture: MainFrameBufferTexture = MainFrameBufferTexture('main', width - 400, height - 200)
        self.textures['main'] = self.main_texture

    def add_texture(self, name, width, height):
        texture = SimpleTexture(name, width, height)
        self.textures[texture.name] = texture

    def del_texture(self, name):
        if name == 'main':
            logging.warning('main texture cannot be deleted')
            return
        texture = self.textures[name]
        self.textures.pop(name)
        del texture

    def get_or_create_texture(self, name, default_width=800, default_height=800) -> SimpleTexture:
        if name not in self.textures:
            self.add_texture(name, default_width, default_height)
        return self.textures[name]

    def bilt_to(self, name, data):
        if name == 'main':
            return
        texture = self.get_or_create_texture(name, data.shape[1], data.shape[0])
        texture.bilt_data(data)

    def plot_to(self, name, gdf, **kwargs):
        print('Simple Texture的plot to功能 目前不再受支持')
        # if name == 'main':
        #     return
        # texture = self.get_or_create_texture(name)
        # texture.plot_gdf(gdf, **kwargs)

    def plot_to2(self, name, plot_func, **kwargs):
        print('Simple Texture的plot to2功能 目前不再受支持')
        # if name == 'main':
        #     return
        # texture = self.get_or_create_texture(name)
        # texture.plot(plot_func, **kwargs)
