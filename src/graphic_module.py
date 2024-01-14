import logging

import matplotlib
import pygame
from OpenGL.GL import *
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from datetime import datetime
from geopandas import GeoDataFrame
import imgui

from style_module import StyleManager, StyleScheme
import utils.common_utils
from utils.common_utils import timer
from utils import RoadCluster, BuildingCluster, RegionCluster
from geo import Road, Building, Region
import cv2
import geopandas as gpd
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _plot_gdf_func(**kwargs):
    assert 'gdf' in kwargs
    assert 'ax' in kwargs
    gdf = kwargs['gdf']
    kwargs.pop('gdf')

    if isinstance(gdf, GeoDataFrame):
        gdf.plot(**kwargs)
    elif isinstance(gdf, list):
        for df in gdf:
            df.plot(**kwargs)


def plot_as_array(gdf, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, **kwargs):
    """kwargs 将会被传递给_plot_gdf_func的gdf.plot方法"""
    return plot_as_array2(_plot_gdf_func, width, height, y_lim, x_lim, transparent, antialiased, gdf=gdf, **kwargs)

@timer
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

@timer
def update_texture(texture_id, data):
    glBindTexture(GL_TEXTURE_2D, texture_id)

    height, width, channels = data.shape

    if channels == 3:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, data)
    elif channels == 4:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, data)

@timer
def blend_img_data(bot, top):
    # 分离 alpha 通道
    bot_a = bot[:, :, 3] / 255.0
    top_a = top[:, :, 3] / 255.0

    bot_rgb = bot[:, :, :3].astype(np.float32)
    top_rgb = top[:, :, :3].astype(np.float32)

    blended_rgb = (1 - top_a[:, :, np.newaxis]) * bot_rgb + top_a[:, :, np.newaxis] * top_rgb

    blended_alpha = bot_a + top_a * (1 - bot_a)
    blended_alpha = blended_alpha * 255
    blended = np.concatenate((blended_rgb, blended_alpha[:, :, np.newaxis]), axis=2)
    blended = blended.astype(np.uint8)
    return blended


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
        self.blank_img_data = None

        self.update_size(width, height)

    def update_size(self, width, height):
        print(f'[update_size]update size to {width}, {height}')
        self.width = width
        self.height = height
        self.blank_img_data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self.texture_id = create_texture_from_array(self.blank_img_data)

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
        update_texture(self.texture_id, data)
        if auto_cache:
            self.cache_data(data)
        self.last_update_time = datetime.now().strftime("%H-%M-%S")

    def cache_data(self, data):
        self.cached_data = data

    def clear_cache(self):
        self.cached_data = None

    def plot_gdf(self, gdf, **kwargs):
        image_data, ax = plot_as_array(gdf, self.width, self.height, y_lim=self.y_lim, **kwargs)
        self.x_lim = ax.get_xlim()
        self.y_lim = ax.get_ylim()
        self.bilt_data(image_data)

    def plot_by_func(self, func, **kwargs):
        image_data, ax = plot_as_array2(func, self.width, self.height, self.y_lim, self.x_lim, **kwargs)
        self.x_lim = ax.get_xlim()
        self.y_lim = ax.get_ylim()
        self.bilt_data(image_data)


class MainGraphTexture(GraphicTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
        self.enable_render_roads = True
        self.enable_render_buildings = False
        self.enable_render_regions = False

        self._road_cluster = RoadCluster()
        self._building_cluster = BuildingCluster()
        self._region_cluster = RegionCluster()

        self._any_change = False
        self.cached_road_data = None
        self.cached_building_data = None
        self.cached_region_data = None
        self.cached_road_idx = None
        self.cached_highlighted_road_data = None

    def show_imgui_display_editor(self):
        road_changed = False
        building_changed = False
        region_changed = False
        clicked, self.enable_render_roads = imgui.checkbox('render roads', True)
        if clicked:
            imgui.open_popup('warning')
        if imgui.begin_popup_modal('warning', flags=imgui.WINDOW_NO_MOVE|imgui.WINDOW_NO_RESIZE|imgui.WINDOW_NO_TITLE_BAR|imgui.WINDOW_ALWAYS_AUTO_RESIZE).opened:
            size = imgui.get_window_size()
            imgui.text('不能关闭道路的显示')
            if imgui.button('知道了', width=size.x-16, height=22):
                imgui.close_current_popup()
            imgui.end_popup()
        if self.enable_render_roads:
            imgui.indent()
            road_changed |= self._road_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        clicked, self.enable_render_buildings = imgui.checkbox('render buildings', self.enable_render_buildings)
        if self.enable_render_buildings:
            imgui.indent()
            building_changed |= self._building_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()
        clicked, self.enable_render_regions = imgui.checkbox('render regions', self.enable_render_regions)
        if self.enable_render_regions:
            imgui.indent()
            region_changed |= self._region_cluster.show_imgui_cluster_editor_button()
            imgui.unindent()

        if road_changed:
            self.clear_road_data()
        if building_changed:
            self.clear_building_data()
        if region_changed:
            self.clear_region_data()


    def plot_gdf(self, gdf, **kwargs):
        logging.warning('main graph texture dose not support plot gdf')

    def _in_regions(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height


    def _wrapped_plot_as_array2(self, plot_func, **kwargs):
        img_data, ax = plot_as_array2(plot_func=plot_func,
                                      width=self.width,
                                      height=self.height,
                                      y_lim=self.y_lim,
                                      transparent=True,
                                      antialiased=False,
                                      **kwargs
                                      )
        return img_data, ax


    def _render_roads(self):
        if self.cached_road_data is None:
            img_data, ax = self._wrapped_plot_as_array2(Road.plot_using_style_factory,
                                                        x_lim=self.x_lim,
                                                        roads=Road.get_roads_by_cluster(self._road_cluster),
                                                        style_factory=StyleManager.instance.display_style.get_current_road_style_factory())
            if self.x_lim is None:
                # 只有在第一次的时候才更新
                self.x_lim = ax.get_xlim()
                self.y_lim = ax.get_ylim()
            self.cached_road_data = img_data
            self._any_change = True
        else:
            img_data = self.cached_road_data
        return img_data


    def _render_buildings(self):
        if self.cached_building_data is None:
            img_data, ax = self._wrapped_plot_as_array2(Building.plot_using_style_factory,
                                                        x_lim=self.x_lim,
                                                        buildings=Building.get_buildings_by_cluster(
                                                            self._building_cluster),
                                                        style_factory=StyleManager.instance.display_style.get_current_building_style_factory())
            self.cached_building_data = img_data
            self._any_change = True
        else:
            img_data = self.cached_building_data
        return img_data


    def _render_regions(self):
        if self.cached_region_data is None:
            img_data, ax = self._wrapped_plot_as_array2(Region.plot_using_style_factory,
                                                        x_lim=self.x_lim,
                                                        regions=Region.get_regions_by_cluster(self._region_cluster),
                                                        style_factory=StyleManager.instance.display_style.get_current_region_style_factory())
            self.cached_region_data = img_data
            self._any_change = True
        else:
            img_data = self.cached_region_data
        return img_data

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
                img_data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            self.cached_highlighted_road_data = img_data
            self._any_change = True
        else:
            img_data = self.cached_highlighted_road_data
        return img_data

    def _get_road_idx(self, idx_img_data, mouse_pos):
        pointer_color = idx_img_data[mouse_pos[1], mouse_pos[0]]
        id = utils.common_utils.rgb_to_id(pointer_color)
        on_road = not np.array_equal(pointer_color, np.array([255, 255, 255, 0]))
        print(f'id = {id}, color = {pointer_color}')
        return on_road, id

    def on_left_mouse_click(self, mouse_pos):
        if self._in_regions(mouse_pos) and self.enable_render_roads:
            idx_img_data = self._render_road_idx()
            on_road, idx = self._get_road_idx(idx_img_data, mouse_pos)
            if on_road:
                self.clear_highlight_data()
            print(f'[on_left_mouse_click] {on_road} {idx}')
            return on_road, idx
        else:
            return False, 0

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

        self._any_change = False
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

        if self._any_change:
            print('[update] new change detected')
            blended = blend_img_data(region_data, building_data)
            blended = blend_img_data(blended, road_data)
            blended = blend_img_data(blended, highlight_data)
            self.bilt_data(blended, auto_cache=False)

    def clear_cache(self):
        self.cached_data = None
        self.cached_road_data = None
        self.cached_road_idx = None
        self.cached_highlighted_road_data = None
        self.cached_building_data = None
        self.cached_region_data = None

    def clear_highlight_data(self):
        self.cached_highlighted_road_data = None

    def clear_road_data(self):
        """适用于road的颜色、显示等发生改变时"""
        self.cached_road_data = None

    def clear_road_data_deep(self):
        """适用于road的文件结构改变时"""
        self.cached_road_data = None
        self.cached_road_idx = None
        self.cached_highlighted_road_data = None

    def clear_building_data(self):
        self.cached_building_data = None

    def clear_region_data(self):
        self.cached_region_data = None
class GraphicManager:
    instance: 'GraphicManager' = None

    def __init__(self):
        GraphicManager.instance = self
        self.textures = {}
        # width, height = pygame.display.get_window_size()
        width = 1920
        height = 1080
        self.main_texture = MainGraphTexture('main', width - 400, height - 200)

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
