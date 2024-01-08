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
from geo import Road
import cv2
import geopandas as gpd


def plot_as_array(gdf, width, height, y_lim=None, **kwargs):
    plt.clf()
    plt.close('all')
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    ax.set_frame_on(True)  # 没有边框
    ax.set_xticks([])  # 没有 x 轴坐标
    ax.set_yticks([])  # 没有 y 轴坐标
    ax.set_aspect('equal')  # 横纵轴比例相同
    fig.patch.set_facecolor('none')  # 设置 figure 的背景色为透明
    ax.patch.set_facecolor('none')  # 设置 axes 的背景色为透明
    fig.tight_layout()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    canvas = FigureCanvas(fig)
    if isinstance(gdf, GeoDataFrame):
        gdf.plot(ax=ax, **kwargs)
    elif isinstance(gdf, list):
        for df in gdf:
            df.plot(ax=ax, **kwargs)

    if y_lim:
        ax.set_ylim(y_lim)

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

    canvas.draw()
    # 从画布中提取图像数据为 NumPy 数组
    image_data = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
    image_data = image_data.reshape(canvas.get_width_height()[::-1] + (4,))
    return image_data, ax


def plot_as_array2(plot_func, width, height, y_lim=None,x_lim=None,transparent=True, **kwargs):
    # 禁用抗锯齿效果
    matplotlib.rcParams['lines.antialiased'] = False
    matplotlib.rcParams['patch.antialiased'] = False

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


    if y_lim:
        ax.set_ylim(y_lim)
    else:
        pass
        # use default y lim

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

    canvas.draw()
    # 从画布中提取图像数据为 NumPy 数组
    image_data = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
    image_data = image_data.reshape(canvas.get_width_height()[::-1] + (4,))

    output_width = image_data.shape[1]
    output_height = image_data.shape[0]
    if output_width != width or output_height != height:
        print('遇到了输出误差，正在自动校准 ')
        # 裁剪多余部分
        if output_width > width:
            image_data = image_data[:,0:width,:]
        if output_height > height:
            image_data = image_data[0:height,:,:]
        # 重新计算大小，此时的imagedata 一定小于等于期望大小
        output_width = image_data.shape[1]
        output_height = image_data.shape[0]
        # 补足不全部分
        if output_width < width or output_height < height:
            new_image = np.zeros((height, width, 4), dtype=np.uint8)
            new_image[0:output_height, 0:output_width, :] = image_data
            image_data = new_image
    return image_data, ax

def tmp(*args, **kwargs):
    # 在每个几何对象上标注序号
    Road.plot_using_idx(*args, **kwargs)
    idx = 0
    ax = kwargs['ax']
    for uid, row in Road.get_all_roads().iterrows():
        line = row['geometry']
        midpoint = line.interpolate(line.length / 2)
        ax.text(midpoint.x, midpoint.y, str(idx), fontsize=10, ha='center', color='orange')
        idx += 1

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
        data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self.texture_id = create_texture_from_array(data)

    def bilt_data(self, data, auto_cache=True):
        if data is None:
            print('data is None')
            return
        width = data.shape[1]
        height = data.shape[0]
        if width != self.width or height != self.height:
            print(f'[bilt_data] input width {width}, self.width {self.width}')
            print(f'[bilt_data] input height { height}, self.height {self.height}')
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

    def plot(self, func, **kwargs):
        image_data, ax = plot_as_array2(func, self.width, self.height, self.y_lim, self.x_lim, **kwargs)
        self.x_lim = ax.get_xlim()
        self.y_lim = ax.get_ylim()
        self.bilt_data(image_data)


class MainGraphTexture(GraphicTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
        self.x_lim = None
        self.y_lim = None

        self._any_change = False
        self.cached_road_data = None
        self.cached_road_idx = None
        self.cached_highlighted_road_data = None

    def plot_gdf(self, gdf, **kwargs):
        logging.warning('main graph texture dose not support plot gdf')

    def _in_regions(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def _render_road(self):
        if self.cached_road_data is None:
            img_data, ax = plot_as_array2(Road.plot_all, self.width, self.height, self.y_lim)
            print(f'[_render_road] ylim (before) {self.y_lim}')
            self.x_lim = ax.get_xlim()
            self.y_lim = ax.get_ylim()
            print(f'[_render_road] ylim (after) {self.y_lim}')
            print(f'[_render_road] data shape {img_data.shape}')
            self.cached_road_data = img_data
            self._any_change = True
        else:
            img_data = self.cached_road_data
        return img_data

    def _render_road_idx(self):
        if self.cached_road_idx is None:
            print(f'[_render_road_idx] render road idx')
            idx_img_data, _ = plot_as_array2(Road.plot_using_idx, self.width, self.height, self.y_lim, self.x_lim, False)
            # idx_img_data2, _ = plot_as_array2(tmp, self.width, self.height, self.y_lim, self.x_lim)
            # GraphicManager.instance.bilt_to('debug idx with number', idx_img_data2)
            # GraphicManager.instance.bilt_to('debug idx color', idx_img_data)
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
                img_data, ax = plot_as_array2(Road.plot_roads, self.width, self.height, self.y_lim, self.x_lim,
                                              roads=roads, colors=(0, 1, 0, 1))
                print(f'[_render_highlighted_road] ylim {self.y_lim}')
                print(f'[_render_highlighted_road] data shape {img_data.shape}')
            else:
                print(f'[_render_highlighted_road] nothing to render, return np.zeros')
                img_data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            self.cached_highlighted_road_data = img_data
            self._any_change = True
        else:
            img_data = self.cached_highlighted_road_data
        return img_data

    def _get_road_idx(self, idx_img_data, mouse_pos):
        pointer_color = idx_img_data[mouse_pos[1], mouse_pos[0]]
        id = pointer_color[0] * 256 * 256 + pointer_color[1] * 256 + pointer_color[2]
        print(f'real id = {id}')
        id = round(id / Road.get_encode_ratio())
        on_road = not np.array_equal(pointer_color, np.array([255,255,255,255]))
        print(f'id = {id}, color = {pointer_color}')
        return on_road, id

    def on_left_mouse_click(self, mouse_pos):
        if self._in_regions(mouse_pos):
            idx_img_data = self._render_road_idx()
            on_road, idx = self._get_road_idx(idx_img_data, mouse_pos)
            if on_road:
                self.clear_highlight_data()
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
            self.bilt_data(blended, auto_cache=False)

    def clear_cache(self):
        self.cached_data = None
        self.cached_road_data = None
        self.cached_road_idx = None
        self.cached_highlighted_road_data = None

    def clear_highlight_data(self):
        self.cached_highlighted_road_data = None


class GraphicManager:
    instance = None

    def __init__(self):
        GraphicManager.instance = self
        self.textures = {}

        width, height = pygame.display.get_window_size()
        self.main_texture = MainGraphTexture('main', width - 400, height - 200)
        self.textures['main'] = self.main_texture

        self.x_lim = None
        self.y_lim = None

    def add_texture(self, name, width, height):
        texture = GraphicTexture(name, width, height)
        self.textures[texture.name] = texture

    def del_texture(self, name):
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
