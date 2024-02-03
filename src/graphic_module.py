import logging
import moderngl
import numpy as np
import imgui
import geopandas as gpd
from typing import *
from gui import global_var as g
from geo import Road, Building, Region
from style_module import StyleManager as sm
from utils import RoadCluster, BuildingCluster, RegionCluster
from utils import graphic_uitls
from gui.icon_module import IconManager
from abc import ABC, abstractmethod

class SimpleTexture:
    def __init__(self, name, width, height, channel=4):
        self.name = name
        self.width, self.height, self.channel = width, height, channel
        self.exposed = True  # 是否暴露给GUI。在GUI上显示需要满足两个条件，一是exposed设为True，二是在GraphicManager的textures中注册
        GraphicManager.I.register_texture(self)
        self.ctx = g.mCtx
        self.texture = self.ctx.texture((width, height), channel, None)
        g.mModernglWindowRenderer.register_texture(self.texture)
        self.x_lim = None
        self.y_lim = None

    @property
    def texture_id(self):
        return self.texture.glo

    def bilt_data(self, data: np.ndarray):
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
    使用modernGL 的 FrameBuffer作为渲染画布的高级Texture对象
    此类为基类， 实现了基础属性的获取与修改，支持改变texture的尺寸并自动注册和销毁
    要对该Texture进行修改，需要继承该类并对render方法进行修改
    """

    def __init__(self, name, width, height, channel=4, exposed=True):
        self.name = name
        self.width, self.height, self.channel = width, height, channel
        self.exposed = exposed
        GraphicManager.I.register_texture(self)
        # 是否暴露给GUI。在GUI上显示需要满足两个条件，一是exposed设为True，二是在GraphicManager的textures中注册
        # 手动直接创建的FrameBufferTexture不会在GraphicManager的textures中注册

        self.x_lim = None  # 世界坐标，显示范围
        self.y_lim = None  # 世界坐标，显示范围

        self.ctx = g.mCtx
        # 新建一个frame buffer object， 在上面进行渲染绘图
        self.fbo = self.ctx.framebuffer(color_attachments=self.ctx.texture((width, height), 4))  # frame buffer object
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

        self.fbo = self.ctx.framebuffer(color_attachments=self.ctx.texture((width, height), 4))
        g.mModernglWindowRenderer.register_texture(self.fbo.color_attachments[0])
        logging.debug(f'texture size updated to {self.width, self.height}, id = {self.fbo.color_attachments[0].glo}')

    @abstractmethod
    def render(self, **kwargs):
        pass


class MainFrameBufferTexture(FrameBufferTexture):
    """主视图 渲染窗口"""

    def __init__(self, name, width, height):
        super().__init__(name, width, height)

        # clusters 过滤器
        self.road_cluster = RoadCluster()
        self.building_cluster = BuildingCluster()
        self.region_cluster = RegionCluster()

        # params
        self.background_color = g.MAIN_FRAME_BUFFER_TEXTURE_BACKGROUND_COLOR  # 渲染视口的背景颜色
        self.enable_render_roads = g.ENABLE_RENDER_ROADS  # 是否渲染道路
        self.enable_render_buildings = g.ENABLE_RENDER_BUILDINGS  # 是否渲染建筑
        self.enable_render_regions = g.ENABLE_RENDER_REGIONS  # 是否渲染区域
        self.enable_render_nodes = g.ENABLE_RENDER_NODES  # 是否渲染节点
        self.enable_mouse_pointer = g.ENABLE_RENDER_MOUSE_POINTER  # 是否显示鼠标光标定位十字
        self.enable_post_processing = g.ENABLE_POST_PROCESSING  # 是否开启后处理

        self._any_change = False  # 是否有任何变化
        self._lazy_update = True  # 设置为True时，只有当有变化发生时才会渲染

        self._need_check_roads = True  # 是否需要检查道路
        self._need_check_buildings = True  # 是否需要检查建筑
        self._need_check_regions = True  # 是否需要检查区域
        self._need_check_nodes = True  # 是否需要检查节点
        self._need_check_highlighted_roads = True  # 是否需要检查高亮道路
        self._need_check_highlighted_nodes = True  # 是否需要检查高亮节点
        self._need_check_road_idx = True  # 是否需要检查道路序号
        self._need_check_node_idx = True  # 是否需要检查节点序号

        # caches 缓存
        self._cached_road_uid = None
        self._cached_building_uid = None
        self._cached_region_uid = None

        # vertex array objects, buffer and programs

        _rosf = sm.I.dis.get_current_road_style_factory()
        _busf = sm.I.dis.get_current_building_style_factory()
        _resf = sm.I.dis.get_current_region_style_factory()
        _nosf = sm.I.dis.node_style_factory
        _rhsf = sm.I.dis.road_highlight_style_factory
        _nhsf = sm.I.dis.node_highlight_style_factory

        self._road_renderer = graphic_uitls.RoadRO('road', _rosf)
        self._building_renderer = graphic_uitls.BuildingRO('building', _busf)
        self._region_renderer = graphic_uitls.RegionRO('region', _resf)
        self._node_renderer = graphic_uitls.NodeRO('node', _nosf)
        self._highlighted_road_renderer = graphic_uitls.RoadRO('highlighted_road', _rhsf)
        self._highlighted_node_renderer = graphic_uitls.NodeRO('highlighted_node', _nhsf)

        # child buffer textures  这些FrameBufferTexture受MainFrameBufferTexture管理
        self._road_idx_texture = RoadIdxFrameBufferTexture('_road_idx', self.width, self.height)
        self._node_idx_texture = NodeIdxFrameBufferTexture('_node_idx', self.width, self.height)

        # post processing 后处理
        self._post_processing = PostProcessing(
            self.width, self.height, self,
            BlurPostProcessing('_blur_h', self.width, self.height, (1.0, 0.0)),
            BlurPostProcessing('_blur_v', self.width, self.height, (0.0, 1.0))
        )

        # imgui draw list  imgui绘制在屏幕上的内容
        self._mouse_pointer = graphic_uitls.ImguiMousePointerScreenSpace()  # 鼠标定位指针
        self._drag_rect = graphic_uitls.ImguiRectScreenSpace()  # 框选
        self._close_node_debug_circles: list[graphic_uitls.ImguiCircleWorldSpace] = []  # 相近节点debug显示
        self._close_node_debug_texts: list[graphic_uitls.ImguiTextWorldSpace] = []  # 相近节点debug显示
        self._intersection_debug_circles: list[graphic_uitls.ImguiCircleWorldSpace] = []  # 相交节点debug显示
        self._intersection_debug_texts: list[graphic_uitls.ImguiTextWorldSpace] = []  # 相交节点debug显示

        # temp  临时缓存变量
        self._cached_drag_selection_start_pos = None  # 拖动开始的位置
        self._cached_road_or_node_idx_img_arr = None  # 拖动开始时缓存的一张idx img arr

    def show_imgui_display_editor(self):
        """imgui 图层显示"""
        road_cluster_changed = False
        building_cluster_changed = False
        region_cluster_changed = False
        # roads 开关
        IconManager.imgui_icon('road-fill')
        imgui.same_line()
        clicked, state = imgui.checkbox('render roads', True)
        if clicked:
            imgui.open_popup('warning')
        flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_ALWAYS_AUTO_RESIZE
        if imgui.begin_popup_modal('warning', flags=flags).opened:
            size = imgui.get_window_size()
            imgui.set_window_position(g.mWindowSize[0] / 2 - size.x / 2, g.mWindowSize[1] / 2 - size.y / 2)
            imgui.text('不能关闭道路的显示')
            if imgui.button('知道了', width=size.x - 16, height=22):
                imgui.close_current_popup()
            imgui.end_popup()
        if self.enable_render_roads:
            imgui.indent()
            road_cluster_changed |= self.road_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        # buildings 开关
        IconManager.imgui_icon('building-fill')
        imgui.same_line()
        clicked, state = imgui.checkbox('render buildings', self.enable_render_buildings)
        if clicked:
            self._any_change = True
            self.enable_render_buildings = state
            g.ENABLE_RENDER_BUILDINGS = state

        if self.enable_render_buildings:
            imgui.indent()
            building_cluster_changed |= self.building_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        # regions 开关
        IconManager.imgui_icon('polygon')
        imgui.same_line()
        clicked, state = imgui.checkbox('render regions', self.enable_render_regions)
        if clicked:
            self._any_change = True
            self.enable_render_regions = state
            g.ENABLE_RENDER_REGIONS = state
        if self.enable_render_regions:
            imgui.indent()
            region_cluster_changed |= self.region_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()

        # nodes 开关
        IconManager.imgui_icon('vector-polygon')
        imgui.same_line()
        clicked, state = imgui.checkbox('render nodes', self.enable_render_nodes)
        if clicked:
            self._any_change = True
            self.enable_render_nodes = state
            g.ENABLE_RENDER_NODES = state

        if road_cluster_changed:
            self.clear_road_data()
        if building_cluster_changed:
            self.clear_building_data()
        if region_cluster_changed:
            self.clear_region_data()

    def show_imgui_main_texture_settings(self):
        """主图形渲染设置"""
        # 渲染分辨率
        changed, value = imgui.drag_float('Resolution Scale', 1 / g.TEXTURE_SCALE, 0.01, 0.1, 2)
        if changed:
            g.TEXTURE_SCALE = 1 / value
        # 指针十字显示
        clicked, state = imgui.checkbox('Show Pointer', self.enable_mouse_pointer)
        if clicked:
            self.enable_mouse_pointer = state
            g.ENABLE_RENDER_MOUSE_POINTER = state
        # 后处理设置
        clicked, state = imgui.checkbox("Enable Post Processing", self.enable_post_processing)
        if clicked:
            self.enable_post_processing = state
            g.ENABLE_POST_PROCESSING = state
        # 背景颜色
        changed, color = imgui.color_edit4("Background Color", *self.background_color)
        if changed:
            self.background_color = color
            g.MAIN_FRAME_BUFFER_TEXTURE_BACKGROUND_COLOR = color

    def _check_roads(self):
        """
        检查roads是否需要更新，两种情况会导致其进行更新操作：
        1. self._need_check_roads被设置为True
        2. Road.uid 发生了变化，此处的uid为Road类的整体uid，当Road类发生任何变化都会使该值发生变化。
           当使用road cluster筛选出特定的道路进行显示时， 当未显示的road发生变化时，也会进行更新
            下述的所有check与之相同，不再赘述
        :return:
        """
        if self._need_check_roads or self._cached_road_uid != Road.uid():

            self._road_renderer.set_gdf(Road.get_roads_by_cluster(self.road_cluster))
            self._road_renderer.set_style_factory(sm.I.dis.get_current_road_style_factory())
            self._road_renderer.update_buffer()

            if self._cached_road_uid != Road.uid():
                # 当road结构发生变化时，将相关变量设为需要检查
                self._need_check_nodes = True
                self._need_check_road_idx = True
                self._need_check_node_idx = True

            self._cached_road_uid = Road.uid()
            self._need_check_roads = False
            self._any_change = True
            return True
        else:
            return False

    def _check_buildings(self):
        if self._need_check_buildings or self._cached_building_uid != Building.uid():
            self._building_renderer.set_gdf(Building.get_buildings_by_cluster(self.building_cluster))
            self._building_renderer.set_style_factory(sm.I.dis.get_current_building_style_factory())
            self._building_renderer.update_buffer()

            self._cached_building_uid = Building.uid()
            self._need_check_buildings = False
            self._any_change = True
            return True
        else:
            return False

    def _check_regions(self):
        if self._need_check_regions or self._cached_region_uid != Region.uid():
            self._region_renderer.set_gdf(Region.get_regions_by_cluster(self.region_cluster))
            self._region_renderer.set_style_factory(sm.I.dis.get_current_region_style_factory())
            self._region_renderer.update_buffer()

            self._cached_region_uid = Region.uid()
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

            self._highlighted_road_renderer.set_gdf(roads)
            self._highlighted_road_renderer.update_buffer()

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

            self._highlighted_node_renderer.set_gdf(nodes)
            self._highlighted_node_renderer.update_buffer()

            self._need_check_highlighted_nodes = False
            self._any_change = True
            return True
        else:
            return False

    def _check_road_idx(self):
        if self._need_check_road_idx:
            self._road_idx_texture.road_idx_renderer.set_gdf(Road.get_roads_by_cluster(self.road_cluster))
            self._road_idx_texture.road_idx_renderer.update_buffer()
            self._need_check_road_idx = False
            self._any_change = True
        else:
            return False

    def _check_node_idx(self):
        if self._need_check_node_idx:
            self._node_idx_texture.node_idx_renderer.set_gdf(Road.get_all_nodes())
            self._node_idx_texture.node_idx_renderer.update_buffer()
            self._need_check_node_idx = False
            self._any_change = True

    def _check_nodes(self):
        if self._need_check_nodes:
            self._node_renderer.set_gdf(Road.get_all_nodes())
            self._node_renderer.set_style_factory(sm.I.dis.node_style_factory)
            self._node_renderer.update_buffer()

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
        self._road_idx_texture.road_idx_renderer.update_prog(self.x_lim, self.y_lim)
        self._road_idx_texture.road_idx_renderer.render()
        texture = self._road_idx_texture.texture
        img_uint8 = np.frombuffer(self._road_idx_texture.fbo.color_attachments[0].read(), dtype=np.uint8).reshape(
            (texture.height, texture.width, 4))
        return img_uint8

    def _render_and_get_node_idx_uint8_img_arr(self):
        self._node_idx_texture.fbo.use()
        self._node_idx_texture.fbo.clear(1, 1, 1, 0)  # 前三个通道表示id， alpha通道表示是否有道路
        self._node_idx_texture.node_idx_renderer.update_prog(self.x_lim, self.y_lim)
        self._node_idx_texture.node_idx_renderer.render()
        texture = self._node_idx_texture.texture
        img_uint8 = np.frombuffer(self._node_idx_texture.fbo.color_attachments[0].read(), dtype=np.uint8).reshape(
            (texture.height, texture.width, 4))
        return img_uint8

    def get_road_or_node_idx_by_mouse_pos(self, texture_space_mouse_pos, select_roads=True) -> Optional[int]:
        """
        根据鼠标位置（图像空间）获取道路或节点的id
        :param texture_space_mouse_pos: 鼠标位置（图像空间）
        :param select_roads: 值为True，则为选择道路模式，否则为选择节点模式
        :return: 被选择的道路idx， 若点击空白或没有图像，则返回None
        """
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
        """
        鼠标开始拖动时的事件， 记录初始位置以及idx图像
        :param texture_space_mouse_pos: 鼠标位置（图像空间）
        :param select_roads: 值为True，则为选择道路模式，否则为选择节点模式
        """
        if not self._in_regions(texture_space_mouse_pos): return
        if self.x_lim is None or self.y_lim is None: return
        self._cached_drag_selection_start_pos = texture_space_mouse_pos
        if select_roads:
            self._cached_road_or_node_idx_img_arr = self._render_and_get_road_idx_uint8_img_arr()
        else:
            self._cached_road_or_node_idx_img_arr = self._render_and_get_node_idx_uint8_img_arr()
        self._any_change = True

    def update_drag_selection(self, image_space_mouse_pos):
        """
        鼠标持续拖动事件， 获取框选范围内的idx列表
        :param image_space_mouse_pos: 鼠标位置（图像空间）
        :return: 被框选的idx list， 失败则返回None
        """
        if self._cached_drag_selection_start_pos is None or self._cached_road_or_node_idx_img_arr is None:
            return None
        x_min = min(image_space_mouse_pos[0], self._cached_drag_selection_start_pos[0])
        x_max = max(image_space_mouse_pos[0], self._cached_drag_selection_start_pos[0])
        y_min = min(image_space_mouse_pos[1], self._cached_drag_selection_start_pos[1])
        y_max = max(image_space_mouse_pos[1], self._cached_drag_selection_start_pos[1])
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
        """鼠标结束拖动的事件"""
        self._cached_drag_selection_start_pos = None
        self._cached_road_or_node_idx_img_arr = None
        self._any_change = True

    def clear_cache(self):
        """清除所有缓存， 全部重新检查并绘制"""
        self.x_lim = None
        self.y_lim = None
        self.recheck_all()

    def recheck_all(self):
        """重新检查所有项目"""
        self._need_check_roads = True
        self._need_check_buildings = True
        self._need_check_regions = True
        self._need_check_nodes = True
        self._need_check_road_idx = True
        self._need_check_node_idx = True
        self._need_check_highlighted_roads = True
        self._need_check_highlighted_nodes = True

    def clear_highlight_data(self):
        """刷新高亮内容"""
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
        """显示区域的宽度（世界空间）"""
        return 0 if self.x_lim is None else self.x_lim[1] - self.x_lim[0]

    @property
    def world_space_height(self):
        """显示区域的高度（世界空间）"""
        return 0 if self.y_lim is None else self.y_lim[1] - self.y_lim[0]

    @property
    def mouse_pos_percent(self):
        """鼠标位置在图像中的百分比"""
        return float(g.mMousePosInImage[0]) / self.width, float(g.mMousePosInImage[1]) / self.height

    def zoom_all(self):
        """重新获取x_lim 和 y_lim，并自动缩放"""
        logging.debug('zoom all')
        x_lim, y_lim = self._road_renderer.get_xy_lim()  # 主要根据road的范围来
        y_center = (y_lim[0] + y_lim[1]) / 2
        y_size = y_lim[1] - y_lim[0]
        y_size *= 1.05  # 略微缩小
        self.y_lim = (y_center - y_size / 2, y_center + y_size / 2)
        x_center = (x_lim[0] + x_lim[1]) / 2
        x_size = self.texture_ratio * y_size
        self.x_lim = (x_center - x_size / 2, x_center + x_size / 2)
        self._any_change = True

    def pan(self, texture_space_delta: tuple):
        """平移"""
        if self.x_lim is None or self.y_lim is None: return
        x_ratio = self.world_space_width / self.width
        y_ratio = self.world_space_height / self.height
        x_delta = texture_space_delta[0] * -x_ratio
        y_delta = texture_space_delta[1] * y_ratio
        self.x_lim = (self.x_lim[0] + x_delta, self.x_lim[1] + x_delta)
        self.y_lim = (self.y_lim[0] + y_delta, self.y_lim[1] + y_delta)
        self._any_change = True

    def zoom(self, texture_space_center: tuple, percent: float):
        """缩放"""
        if self.x_lim is None or self.y_lim is None: return
        if percent == 0: return

        ts_cx = texture_space_center[0]  # texture space - center x
        ts_cy = self.height - texture_space_center[1]  # texture space - center y
        ws_cx = self.world_space_width * ts_cx / self.width + self.x_lim[0]  # world space - center x
        ws_cy = self.world_space_height * ts_cy / self.height + self.y_lim[0]  # world space - center y

        # 归零
        nx, px = self.x_lim[0] - ws_cx, self.x_lim[1] - ws_cx  # negative x,  positive x
        ny, py = self.y_lim[0] - ws_cy, self.y_lim[1] - ws_cy  # negative y,  positive y

        # 缩放
        nx, px, ny, py = nx * percent, px * percent, ny * percent, py * percent

        self.x_lim, self.y_lim = (ws_cx + nx, ws_cx + px), (ws_cy + ny, ws_cy + py)
        self._any_change = True

    def add_close_node_debug_circle(self, world_x, world_y, screen_radius, color, content):
        """添加相近节点的debug 圆圈显示"""
        circle = graphic_uitls.ImguiCircleWorldSpace(
            world_x, world_y, screen_radius, color, g.mImageWindowDrawList, self)
        text = graphic_uitls.ImguiTextWorldSpace(
            world_x, world_y, content, color, g.mImageWindowDrawList, self)

        self._close_node_debug_circles.append(circle)
        self._close_node_debug_texts.append(text)

    def clear_close_node_debug_circles(self):
        self._close_node_debug_circles = []
        self._close_node_debug_texts = []

    def add_intersection_debug_circle(self, world_x, world_y, screen_radius, tuple_color, content):
        circle = graphic_uitls.ImguiCircleWorldSpace(
            world_x, world_y, screen_radius, tuple_color, g.mImageWindowDrawList, self)
        text = graphic_uitls.ImguiTextWorldSpace(
            world_x, world_y, content, tuple_color, g.mImageWindowDrawList, self)

        self._intersection_debug_circles.append(circle)
        self._intersection_debug_texts.append(text)

    def clear_intersection_debug_circles(self):
        self._intersection_debug_circles = []
        self._intersection_debug_texts = []

    def get_final_texture_id(self):
        """由于这个类还包含了其他渲染的frame buffer， 因此需要通过这个方法取出最终的渲染buffer"""
        if self.enable_post_processing:
            return self._post_processing.texture_id
        else:
            return self.texture_id

    def get_final_frame_buffer(self):
        if self.enable_post_processing:
            return self._post_processing  # 这个不是一个frame buffer  而是多个frame buffer的合集，但是功能是一样的
        else:
            return self
    def render(self, **kwargs):
        """在self.fbo 画布上进行渲染。被调用即进行渲染，不进行逻辑判断
        该方法继承自基类的render"""
        self.fbo.use()  # 使用画布
        self.fbo.clear(*self.background_color)  # 清空画布
        if self.x_lim is None:  # 只有在x_lim被清空 或第一次运行时才会自动缩放
            self.zoom_all()
        # 渲染顺序
        # region - building - road - (highlighted road) - node - (highlighted node) - mouse_pointer - rect
        # 先渲染的物体会置于底层
        if self.enable_render_regions:
            self._region_renderer.update_prog(self.x_lim, self.y_lim)
            self._region_renderer.render()
        if self.enable_render_buildings:
            self._building_renderer.update_prog(self.x_lim, self.y_lim)
            self._building_renderer.render()
        if self.enable_render_roads:
            self._road_renderer.update_prog(self.x_lim, self.y_lim)
            self._road_renderer.render()
            self._highlighted_road_renderer.update_prog(self.x_lim, self.y_lim)
            self._highlighted_road_renderer.render()
        if self.enable_render_nodes:
            self._node_renderer.update_prog(self.x_lim, self.y_lim)
            self._node_renderer.render()
            self._highlighted_node_renderer.update_prog(self.x_lim, self.y_lim)
            self._highlighted_node_renderer.render()

        # 渲染后处理
        self._post_processing.render()

    def update(self, **kwargs):
        """每帧调用"""
        if len(Road.get_all_roads()) == 0:
            return
        width, height = g.mImageSize
        if width != self.width or height != self.height:
            self.update_size(width, height)
            self._road_idx_texture.update_size(width, height)
            self._node_idx_texture.update_size(width, height)
            self._post_processing.update_size(width, height)

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
        if self.enable_mouse_pointer:
            self._mouse_pointer.draw()

        if self._cached_drag_selection_start_pos is not None:
            self._drag_rect.draw(self._cached_drag_selection_start_pos, g.mMousePosInImage)


class RoadIdxFrameBufferTexture(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height, exposed=False)
        self.road_idx_renderer = graphic_uitls.RoadRO('road_idx', sm.I.dis.road_idx_style_factory)


class NodeIdxFrameBufferTexture(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height, exposed=False)
        self.node_idx_renderer = graphic_uitls.NodeRO('node_idx', sm.I.dis.node_idx_style_factory)


class PPStepTemplate(FrameBufferTexture):
    """后处理渲染的步骤(模板)"""

    def __init__(self, name, width, height, program_path):
        super().__init__(name, width, height, exposed=False)  # 所有的后处理步骤默认都不暴露给GUI
        self.renderer = graphic_uitls.FullScreenRO(program_path)

    def update_prog(self, key, value):
        self.renderer.update_prog(key, value)

    def render(self, in_texture: Union[moderngl.Texture, list[moderngl.Texture]], location: Union[int, list[int]]):
        """
        :param in_texture: 输入的texture, 将被传入shader的sampler2D变量
        :param location: 位置
        """
        self.fbo.use()
        self.fbo.clear()
        # 这里将in_texture作为参数传入
        if isinstance(in_texture, list) and isinstance(location, list) and len(in_texture) == len(location):
            for i in range(len(in_texture)):
                in_texture[i].use(location[i])
        else:
            in_texture.use(location)
        self.renderer.render()


class BlurPostProcessing(PPStepTemplate):
    """模糊后处理"""

    def __init__(self, name, width, height, direction):
        """
        :param direction: (1, 0) or (0, 1)
        """
        super().__init__(name, width, height, "programs/blur.glsl")
        self.update_prog("direction", (float(direction[0]) / width, float(direction[1]) / height))


class ShaderPostProcessing(PPStepTemplate):
    """将接收到的纹理颜色映射到frag color"""

    def __init__(self, name, width, height):
        super().__init__(name, width, height, "programs/shader.glsl")


class PostProcessing:
    def __init__(self, width, height, in_frame_buffer, *steps):
        """
        :param in_frame_buffer: FrameBufferTexture类及其子类， 或者PostProcessing类
        :param steps: PPStepTemplate类，数量不限， 按顺序排列
        使用示例：
        (self属于FrameBufferTexture类)
        self._post_processing = PostProcessing(
        self.width, self.height, self,
        BlurPostProcessing('blur1', self.width, self.height, (1.0, 0.0)),
        BlurPostProcessing('blur2', self.width, self.height, (0.0, 1.0))
        )
        """
        self.width = width
        self.height = height
        self.in_frame_buffer = in_frame_buffer
        self.steps = list(steps)
        # self.steps.append(ShaderPostProcessing('shader', width, height))

    def update_size(self, width, height):
        self.width = width
        self.height = height
        for step in self.steps:
            step.update_size(width, height)

    def render(self):
        """仅支持一个Sample2D纹理输入的后处理shader"""
        texture = self.in_frame_buffer.texture
        for step in self.steps:
            step.render(texture, 0)
            texture = step.texture

    @property
    def texture(self):
        return self.steps[-1].texture

    @property
    def texture_id(self):
        return self.texture.glo


class ImguiWindowBlurLayer(PostProcessing):
    def __init__(self, name, width, height):
        super().__init__(width, height,
                         GraphicManager.I.MainTexture.get_final_frame_buffer(),
                         BlurPostProcessing(f'{name}_blur_h', width, height, (1.0, 0.0)),
                         BlurPostProcessing(f'{name}_blur_v', width, height, (0.0, 1.0))
                         )

    def update(self):
        width, height = g.mImageSize
        if width != self.width or height != self.height:
            self.update_size(width, height)
        self.render()


class AgentFrameBufferTexture(FrameBufferTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
        self.exposed = False

        _rsf = sm.I.env.road_level_style_factory
        _bsf = sm.I.env.building_movable_style_factory
        _resf = sm.I.env.region_accessible_style_factory

        self.road_gl = graphic_uitls.RoadRO('road', _rsf)
        self.building_gl = graphic_uitls.BuildingRO('building', _bsf)
        self.region_gl = graphic_uitls.RegionRO('region', _resf)

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
    I: 'GraphicManager' = None  # 实例化

    def __init__(self):
        GraphicManager.I = self
        self.textures = {}
        width, height = g.mWindowSize  # 这里不能设置为mImageSize 因为此时这个变量还没获取
        self.MainTexture: MainFrameBufferTexture = MainFrameBufferTexture('main', width, height)
        self.ImguiBlurLayer = ImguiWindowBlurLayer('imgui_blur', width, height)

    def register_texture(self, texture):
        self.textures[texture.name] = texture

    def unregister_texture(self, name):
        if name == 'main':
            logging.warning('Main FrameBufferTexture cannot be unregistered')
            return
        if name not in self.textures.keys():
            logging.warning(f'cannot find {name} in textures')
            return
        texture = self.textures[name]
        if isinstance(texture, FrameBufferTexture):
            logging.warning('FrameBufferTexture cannot be unregistered')
            return
        self.textures.pop(name)

    def get_or_create_simple_texture(self, name, default_width=800, default_height=800) -> SimpleTexture:
        if name not in self.textures:
            SimpleTexture(name, default_width, default_height)
        return self.textures[name]

    def bilt_to(self, name, data):
        if name == 'main':
            return
        texture = self.get_or_create_simple_texture(name, data.shape[1], data.shape[0])
        texture.bilt_data(data)
