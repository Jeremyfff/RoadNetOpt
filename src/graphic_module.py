import logging
import matplotlib
from OpenGL.GL import *
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
from datetime import datetime
from geopandas import GeoDataFrame
import imgui
<<<<<<< Updated upstream
<<<<<<< HEAD

from style_module import StyleManager, PlotStyle
import utils.common_utils
from geo import Road
import cv2
=======
>>>>>>> Stashed changes
import geopandas as gpd
=======
import geopandas as gpd
import torch
from typing import *

from geo import Road, Building, Region
from style_module import StyleManager
from utils import RoadCluster, BuildingCluster, RegionCluster
from utils import common_utils
from utils.common_utils import timer
from utils import graphic_uitls
from gui.icon_module import IconManager, Spinner
<<<<<<< Updated upstream
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
>>>>>>> Stashed changes

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def plot_as_array(gdf, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, tensor=True,
                  **kwargs):
    logging.warning(
        'graphic_modlue.plot_as_array功能已被迁移至graphic_uitls中，请使用graphic_uitls.plot_as_array\n您调用的方法将在未来被删除，请及时调整代码')
    return graphic_uitls.plot_as_array(gdf, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False,
                                       tensor=True,
                                       **kwargs)


<<<<<<< Updated upstream
<<<<<<< HEAD
def plot_as_array(gdf, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, **kwargs):
    """kwargs 将会被传递给_plot_gdf_func的gdf.plot方法"""
    return plot_as_array2(_plot_gdf_func, width, height, y_lim, x_lim, transparent, antialiased, gdf=gdf, **kwargs)


def plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, **kwargs):
    # 禁用/启用抗锯齿效果
    matplotlib.rcParams['lines.antialiased'] = antialiased
    matplotlib.rcParams['patch.antialiased'] = antialiased

    plt.clf()
    plt.close('all')
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    if transparent:
        fig.patch.set_facecolor('none')  # 设置 figure 的背景色为透明
        ax.patch.set_facecolor('none')  # 设置 axes 的背景色为透明
    ax.set_xticks([])  # 没有 x 轴坐标
    ax.set_yticks([])  # 没有 y 轴坐标
    ax.set_aspect('equal')  # 横纵轴比例相同
    ax.set_facecolor('none')  # 设置图形背景为透明
    fig.tight_layout()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    canvas = FigureCanvas(fig)

    plot_func(ax=ax, **kwargs)

    # 如果指定了y lim， 则使用指定的y lim， 否则将由matplotlib自动计算y lim
    if y_lim:
        ax.set_ylim(y_lim)
    else:
        pass
        # use default y lim
    # 如果指定了x lim，则使用指定的x lim，如果x lim和y lim的比例与图像的宽高比不同，图像将保持在中间，将会造成坐标空间映射的不准确
    # 将x lim留空以让程序自动根据图像宽高比计算x lim
    if x_lim:
        ax.set_xlim(x_lim)
    else:
        # calculate x lim by y lim
        x_range = ax.get_xlim()
        x_min = x_range[0]
        x_max = x_range[1]
        y_range = ax.get_ylim()
        y_min = y_range[0]
        y_max = y_range[1]

        y_width = y_max - y_min
        new_x_width = width / height * y_width

        x_center = (x_min + x_max) / 2
        new_x_range = (x_center - new_x_width / 2, x_center + new_x_width / 2)
        ax.set_xlim(new_x_range)

    canvas.draw()  # 绘制到画布上

    # 从画布中提取图像数据为 NumPy 数组
    image_data = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
    image_data = image_data.reshape(canvas.get_width_height()[::-1] + (4,))

    # 校准输出尺寸
    output_width = image_data.shape[1]
    output_height = image_data.shape[0]
    if output_width != width or output_height != height:
        print('遇到了输出误差，正在自动校准 ')
        # 裁剪多余部分
        if output_width > width:
            image_data = image_data[:, 0:width, :]
        if output_height > height:
            image_data = image_data[0:height, :, :]
        # 重新计算大小，此时的imagedata 一定小于等于期望大小
        output_width = image_data.shape[1]
        output_height = image_data.shape[0]
        # 补足不全部分
        if output_width < width or output_height < height:
            new_image = np.zeros((height, width, 4), dtype=np.uint8)
            new_image[0:output_height, 0:output_width, :] = image_data
            image_data = new_image
    return image_data, ax


def world_space_to_image_space(world_x, world_y, x_lim, y_lim, image_width, image_height):
    assert x_lim[1] - x_lim[0] > 0
    assert y_lim[1] - y_lim[0] > 0

    image_x = int((world_x - x_lim[0]) / (x_lim[1] - x_lim[0]) * image_width)
    image_y = int((world_y - y_lim[0]) / (y_lim[1] - y_lim[0]) * image_height)
    return image_x, image_y


def image_space_to_world_space(image_x, image_y, x_lim, y_lim, image_width, image_height):
    assert image_width != 0
    assert image_height != 0
    world_x = (image_x / image_width) * (x_lim[1] - x_lim[0]) + x_lim[0]
    world_y = (image_y / image_height) * (y_lim[1] - y_lim[0]) + y_lim[0]
    return world_x, world_y


def create_texture_from_array(data):
    height, width, channels = data.shape

    # 生成纹理对象
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    # 设置纹理参数
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # 将数据上传到纹理
    if channels == 3:
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
    elif channels == 4:
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

    return texture_id


def update_texture(texture_id, data):
    glBindTexture(GL_TEXTURE_2D, texture_id)

    height, width, channels = data.shape

    if channels == 3:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, data)
    elif channels == 4:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, data)
=======
@timer
def plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, tensor=True,
                   **kwargs):
    logging.warning(
        'graphic_modlue.plot_as_array2功能已被迁移至graphic_uitls中，请使用graphic_uitls.plot_as_array2\n您调用的方法将在未来被删除，请及时调整代码')
<<<<<<< Updated upstream
    return graphic_uitls.plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, tensor=True,
                   **kwargs)

>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
@timer
def plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, tensor=True,
                   **kwargs):
    logging.warning(
        'graphic_modlue.plot_as_array2功能已被迁移至graphic_uitls中，请使用graphic_uitls.plot_as_array2\n您调用的方法将在未来被删除，请及时调整代码')
    return graphic_uitls.plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, tensor=True,
                   **kwargs)

>>>>>>> Stashed changes
=======
    return graphic_uitls.plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True,
                                        antialiased=False, tensor=True,
                                        **kwargs)
>>>>>>> Stashed changes


class GraphicTexture:
    def __init__(self, name, width, height):
        self.name = name
        self.width = None
        self.height = None
        self.texture_id = None
        self.last_update_time = None
        self.x_lim = None
        self.y_lim = None
        self.exposed = True
        self.cached_data = None
        self.update_size(width, height)

    def update_size(self, width, height):
        print(f'[update_size]update size to {width}, {height}')
        self.width = width
        self.height = height
<<<<<<< Updated upstream
<<<<<<< HEAD
        data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self.texture_id = create_texture_from_array(data)
=======
        self.blank_img_data = torch.zeros((self.height, self.width, 4), dtype=torch.uint8)
        self.texture_id = graphic_uitls.create_texture_from_array(self.blank_img_data)
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
        self.blank_img_data = torch.zeros((self.height, self.width, 4), dtype=torch.uint8)
        self.texture_id = graphic_uitls.create_texture_from_array(self.blank_img_data)
>>>>>>> Stashed changes

    def bilt_data(self, data, auto_cache=True):
        if data is None:
            print('data is None')
            return
        width = data.shape[1]
        height = data.shape[0]
        if width != self.width or height != self.height:
            print(f'[bilt_data] input width {width}, self.width {self.width}')
            print(f'[bilt_data] input height {height}, self.height {self.height}')
            print(f'[bilt_data] bilt data过程中self.size 与input data的size不匹配')
            self.update_size(width, height)
            print(f'[bilt_data] self.size updated to {self.width}, {self.height}')
        graphic_uitls.update_texture(self.texture_id, data)
        if auto_cache:
            self.cache_data(data)
        self.last_update_time = datetime.now().strftime("%H-%M-%S")

    def cache_data(self, data):
        self.cached_data = data

    def clear_cache(self):
        self.cached_data = None

    def plot_gdf(self, gdf, **kwargs):
        image_data, ax = graphic_uitls.plot_as_array(gdf, self.width, self.height, y_lim=self.y_lim, **kwargs)
        self.x_lim = ax.get_xlim()
        self.y_lim = ax.get_ylim()
        self.bilt_data(image_data)

    def plot_by_func(self, func, **kwargs):
        image_data, ax = graphic_uitls.plot_as_array2(func, self.width, self.height, self.y_lim, self.x_lim, **kwargs)
        self.x_lim = ax.get_xlim()
        self.y_lim = ax.get_ylim()
        self.bilt_data(image_data)


class MainGraphTexture(GraphicTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
<<<<<<< Updated upstream
        self.x_lim = None
        self.y_lim = None
=======
        self.enable_render_roads = True
        self.enable_render_buildings = False
        self.enable_render_regions = False
        self.enable_render_nodes = False

        self._road_cluster = RoadCluster()
        self._building_cluster = BuildingCluster()
        self._region_cluster = RegionCluster()
>>>>>>> Stashed changes

        self._any_change = False

        self.cached_road_data = None
<<<<<<< Updated upstream
=======
        self.cached_node_data = None
        self.cached_building_data = None
        self.cached_region_data = None
>>>>>>> Stashed changes
        self.cached_road_idx = None
        self.cached_highlighted_road_data = None

<<<<<<< Updated upstream
<<<<<<< HEAD
=======
=======
>>>>>>> Stashed changes
        self.cached_road_uid = None
        self.cached_building_uid = None
        self.cached_region_uid = None

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
            imgui.text('不能关闭道路的显示')
            if imgui.button('知道了', width=size.x - 16, height=22):
                imgui.close_current_popup()
            imgui.end_popup()
        if self.enable_render_roads:
            imgui.indent()
            road_changed |= self._road_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        # buildings
        IconManager.imgui_icon('building-fill')
        imgui.same_line()
        clicked, self.enable_render_buildings = imgui.checkbox('render buildings', self.enable_render_buildings)
        if clicked:
            self._any_change = True
        if self.enable_render_buildings:
            imgui.indent()
            building_changed |= self._building_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        # regions
        IconManager.imgui_icon('polygon')
        imgui.same_line()
        clicked, self.enable_render_regions = imgui.checkbox('render regions', self.enable_render_regions)
        if clicked:
            self._any_change = True
        if self.enable_render_regions:
            imgui.indent()
            region_changed |= self._region_cluster.show_imgui_cluster_editor_button()
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

<<<<<<< Updated upstream
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
>>>>>>> Stashed changes
    def plot_gdf(self, gdf, **kwargs):
        logging.warning('main graph texture dose not support plot gdf')


    def _in_regions(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def _wrapped_plot_as_array2(self, plot_func, **kwargs):
        img_data, ax = graphic_uitls.plot_as_array2(plot_func=plot_func,
                                                    width=self.width,
                                                    height=self.height,
                                                    y_lim=self.y_lim,
                                                    transparent=True,
                                                    antialiased=False,
                                                    **kwargs
                                                    )
        return img_data, ax
<<<<<<< Updated upstream
<<<<<<< HEAD
    def _render_road(self):
        if self.cached_road_data is None:
=======

    def _render_roads(self):
        if self.cached_road_data is None or self.cached_road_uid != Road.uid():
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======

    def _render_roads(self):
        if self.cached_road_data is None or self.cached_road_uid != Road.uid():
>>>>>>> Stashed changes
            img_data, ax = self._wrapped_plot_as_array2(Road.plot_using_style_factory,
                                                        roads=Road.get_all_roads(),
                                                        style_factory=StyleManager.instance.display_style.get_current_road_style_factory())
            self.x_lim = ax.get_xlim()
            self.y_lim = ax.get_ylim()
            self.cached_road_data = img_data
            self.cached_road_uid = Road.uid()
            self._any_change = True
            self.cached_road_idx = None
            self.cached_node_data = None
        else:
            img_data = self.cached_road_data
        return img_data

<<<<<<< Updated upstream
<<<<<<< HEAD
=======
=======
>>>>>>> Stashed changes
    def _render_buildings(self):
        if self.cached_building_data is None or self.cached_building_uid != Building.uid():
            img_data, ax = self._wrapped_plot_as_array2(Building.plot_using_style_factory,
                                                        x_lim=self.x_lim,
                                                        buildings=Building.get_buildings_by_cluster(
                                                            self._building_cluster),
                                                        style_factory=StyleManager.instance.display_style.get_current_building_style_factory())
            self.cached_building_data = img_data
            self.cached_building_uid = Building.uid()
            self._any_change = True
        else:
            img_data = self.cached_building_data
        return img_data

    def _render_regions(self):
        if self.cached_region_data is None or self.cached_region_uid != Region.uid():
            img_data, ax = self._wrapped_plot_as_array2(Region.plot_using_style_factory,
                                                        x_lim=self.x_lim,
                                                        regions=Region.get_regions_by_cluster(self._region_cluster),
                                                        style_factory=StyleManager.instance.display_style.get_current_region_style_factory())
            self.cached_region_data = img_data
            self.cached_region_uid = Region.uid()
            self._any_change = True
        else:
            img_data = self.cached_region_data
        return img_data
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)

    def _render_road_idx(self):
        if self.cached_road_idx is None:
            print(f'[_render_road_idx] render road idx')
            idx_img_data, _ = self._wrapped_plot_as_array2(Road.plot_using_idx,
                                                           x_lim=self.x_lim,
                                                           roads=Road.get_all_roads())
            self.cached_road_idx = idx_img_data
        else:
            idx_img_data = self.cached_road_idx
        return idx_img_data

    def _render_highlighted_road(self, roads_dict):

        if self.cached_highlighted_road_data is None:
            print(f'[_render_highlighted_road] render highlighted road')
            keys = roads_dict.keys()
            if len(keys) > 0:
                if len(keys) == 1:
                    roads = list(roads_dict.values())[0]
                    roads = roads.to_frame().T
                else:
                    roads = [road.to_frame().T for road in list(roads_dict.values())]
                    roads = gpd.pd.concat(roads, ignore_index=False)
                img_data, ax = self._wrapped_plot_as_array2(Road.plot_roads,
                                                            x_lim=self.x_lim,
                                                            roads=roads,
                                                            colors=(0, 1, 0, 1))

            else:
                img_data = torch.zeros((self.height, self.width, 4), dtype=torch.uint8)
            self.cached_highlighted_road_data = img_data
            self._any_change = True
        else:
            img_data = self.cached_highlighted_road_data
        return img_data

<<<<<<< Updated upstream
    def _get_road_idx(self, idx_img_data, mouse_pos):
<<<<<<< Updated upstream
<<<<<<< HEAD
        pointer_color = idx_img_data[mouse_pos[1], mouse_pos[0]]
        id = utils.common_utils.rgb_to_id(pointer_color)
        on_road = not np.array_equal(pointer_color, np.array([255, 255, 255, 255]))
=======
        pointer_color = idx_img_data[mouse_pos[1], mouse_pos[0]].cpu().numpy()
        id = common_utils.rgb_to_id(pointer_color)
        on_road = pointer_color[3].item() != 0
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
        pointer_color = idx_img_data[mouse_pos[1], mouse_pos[0]].cpu().numpy()
        id = common_utils.rgb_to_id(pointer_color)
        on_road = pointer_color[3].item() != 0
>>>>>>> Stashed changes
        print(f'id = {id}, color = {pointer_color}')
        return on_road, id

    def on_left_mouse_click(self, mouse_pos):
        if self._in_regions(mouse_pos):
            idx_img_data = self._render_road_idx()
            on_road, idx = self._get_road_idx(idx_img_data, mouse_pos)
            if on_road:
                self.clear_highlight_data()
            return on_road, idx
=======
    def _render_nodes(self):
        if self.cached_node_data is None:
            img_data, ax = self._wrapped_plot_as_array2(Road.plot_nodes,
                                                        x_lim=self.x_lim,
                                                        nodes=Road.get_all_nodes(),
                                                        )
            self.cached_node_data = img_data
            self._any_change = True
            return img_data
>>>>>>> Stashed changes
        else:
            return self.cached_node_data

    def get_road_idx_by_mouse_pos(self, mouse_pos) -> Union[int, None]:
        if not self._in_regions(mouse_pos) or not self.enable_render_roads:
            return None
        idx_img_data = self._render_road_idx()
        pointer_color = idx_img_data[mouse_pos[1], mouse_pos[0]].cpu().numpy()
        idx = common_utils.rgb_to_id(pointer_color)
        on_road = pointer_color[3].item() != 0
        if not on_road:
            return None
        # print(f'id = {idx}, color = {pointer_color}')
        return idx

    def update(self, **kwargs):
        if Road.get_all_roads().empty:
            return
        window_size = kwargs['window_size']
        selected_roads = kwargs['selected_roads']
        window_width, window_height = window_size[0], window_size[1]
        if window_width != self.width or window_height != self.height:
            self.update_size(window_width, window_height)
            self.clear_cache()
            print(f'[update] window size changed to {window_width}, {window_height}')
            print(f'[update] self.size updated to {self.width}, {self.height}')
            print(f'[update] return')
            return
<<<<<<< Updated upstream
<<<<<<< HEAD
        self._any_change = False
        road_data = self._render_road()
        highlight_data = self._render_highlighted_road(selected_roads)

        if self._any_change:
            print('[update] new change detected')
            # 分离 alpha 通道
            alpha_channel1 = road_data[:, :, 3] / 255.0
            alpha_channel2 = highlight_data[:, :, 3] / 255.0

            rgb_channel1 = road_data[:, :, :3].astype(np.float32)
            rgb_channel2 = highlight_data[:, :, :3].astype(np.float32)

            blended_rgb = (1 - alpha_channel2[:, :, np.newaxis]) * rgb_channel1 + alpha_channel2[:, :,
                                                                                  np.newaxis] * rgb_channel2

            blended_alpha = alpha_channel1 + alpha_channel2 * (1 - alpha_channel1)
            blended_alpha = blended_alpha * 255
            blended = np.concatenate((blended_rgb, blended_alpha[:, :, np.newaxis]), axis=2)
            blended = blended.astype(np.uint8)

            height, width, channels = blended.shape
            if channels == 3:
                # 创建一个新的 4 通道的数组，初始值为 255（不透明）
                new_image = np.ones((height, width, 4), dtype=np.uint8) * 255
                # 将原始 RGB 数据复制到新数组的前 3 个通道
                new_image[:, :, :3] = blended
                blended = new_image
            print(f'[update] blend data size {blended.shape}')
            print(f'[update] {blended}')
=======
=======
>>>>>>> Stashed changes

        if self.enable_render_roads:
            road_data = self._render_roads()
            highlight_data = self._render_highlighted_road(selected_roads)
        else:
            road_data = self.blank_img_data
            highlight_data = self.blank_img_data

        if self.enable_render_buildings:
            building_data = self._render_buildings()
        else:
            building_data = self.blank_img_data

        if self.enable_render_regions:
            region_data = self._render_regions()
        else:
            region_data = self.blank_img_data

        if self.enable_render_nodes:
            node_data = self._render_nodes()
        else:
            node_data = self.blank_img_data

        if self._any_change:
            print('[update] new change detected')
            blended = graphic_uitls.blend_img_data(region_data, building_data)
            blended = graphic_uitls.blend_img_data(blended, road_data)
            blended = graphic_uitls.blend_img_data(blended, highlight_data)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
>>>>>>> Stashed changes
=======
            if self.enable_render_nodes:
                blended = graphic_uitls.blend_img_data(blended,node_data)
>>>>>>> Stashed changes
            self.bilt_data(blended, auto_cache=False)

        self._any_change = False  # reset to False
    def clear_cache(self):
        self.cached_data = None
        self.cached_road_data = None
        self.cached_road_idx = None
        self.cached_highlighted_road_data = None
<<<<<<< Updated upstream
=======
        self.cached_building_data = None
        self.cached_region_data = None
        self.x_lim = None
        self.y_lim = None
>>>>>>> Stashed changes

    def clear_highlight_data(self):
        self.cached_highlighted_road_data = None



<<<<<<< HEAD
=======
    def clear_building_data(self):
        self.cached_building_data = None

    def clear_region_data(self):
        self.cached_region_data = None

<<<<<<< Updated upstream

>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
    def clear_x_y_lim(self):
        self.x_lim = None
        self.y_lim = None

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
class GraphicManager:
    instance = None

    def __init__(self):
        GraphicManager.instance = self
        self.textures = {}
        # width, height = pygame.display.get_window_size()
        width = 1920
        height = 1080
        self.main_texture: MainGraphTexture = MainGraphTexture('main', width - 400, height - 200)

        self.textures['main'] = self.main_texture

        self.x_lim = None
        self.y_lim = None

    def add_texture(self, name, width, height):
        texture = GraphicTexture(name, width, height)
        self.textures[texture.name] = texture

    def del_texture(self, name):
        if name == 'main':
            logging.warning('main texture cannot be deleted')
            return
        texture = self.textures[name]
        self.textures.pop(name)
        del texture

    def get_or_create_texture(self, name, default_width=800, default_height=800) -> GraphicTexture:
        if name not in self.textures:
            self.add_texture(name, default_width, default_height)
        return self.textures[name]

    def bilt_to(self, name, data):
        if name == 'main':
            return
        texture = self.get_or_create_texture(name, data.shape[0], data.shape[1])
        texture.bilt_data(data)

    def plot_to(self, name, gdf, **kwargs):
        if name == 'main':
            return
        texture = self.get_or_create_texture(name)
        texture.plot_gdf(gdf, **kwargs)

    def plot_to2(self, name, plot_func, **kwargs):
        if name == 'main':
            return
        texture = self.get_or_create_texture(name)
        texture.plot(plot_func, **kwargs)

    def update_main(self, **kwargs):
        self.main_texture.update(**kwargs)


