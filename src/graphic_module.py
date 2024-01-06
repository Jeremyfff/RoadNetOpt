import logging

import pygame
from OpenGL.GL import *
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from datetime import datetime
from geopandas import GeoDataFrame

from geo import Road


def plot_as_array(gdf, width, height, x_lim=None, y_lim=None, **kwargs):
    plt.clf()
    plt.close('all')
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    ax.set_frame_on(True)  # 没有边框
    ax.set_xticks([])  # 没有 x 轴坐标
    ax.set_yticks([])  # 没有 y 轴坐标
    ax.set_aspect('equal')  # 横纵轴比例相同
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
    if x_lim:
        ax.set_xlim(x_lim)

    canvas.draw()
    # 从画布中提取图像数据为 NumPy 数组
    image_data = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8)
    print(f'canvas width height = {canvas.get_width_height()}')
    image_data = image_data.reshape(canvas.get_width_height()[::-1] + (4,))
    print(f'image data size = {image_data.shape}')
    return image_data, ax


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
        self.update_size(width, height)

    def update_size(self, width, height):
        print(f'update size to {width}, {height}')
        self.width = width
        self.height = height
        data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self.texture_id = create_texture_from_array(data)

    def bilt_data(self, data):
        width = data.shape[1]
        height = data.shape[0]
        print('bilt data')
        print(f'data size = {data.shape}. width: {width}, height: {height}')
        if width != self.width or height != self.height:
            print(f'org size = {self.width}, {self.height}')
            self.update_size(width, height)
        update_texture(self.texture_id, data)
        self.last_update_time = datetime.now().strftime("%H-%M-%S")

    def plot_gdf(self, gdf, **kwargs):
        image_data, ax = plot_as_array(gdf, self.width, self.height, **kwargs)
        self.bilt_data(image_data)


class MainGraphTexture(GraphicTexture):
    def __init__(self, name, width, height):
        super().__init__(name, width, height)
        self.x_lim = None
        self.y_lim = None

    def plot_gdf(self, gdf, x_lim, y_lim, **kwargs):
        logging.warning('main graph texture dose not support plot gdf')

    def update(self):
        if Road.get_all_roads().empty:
            return

        image_data, ax = plot_as_array(Road.get_all_roads(), self.width, self.height)
        self.bilt_data(image_data)
        self.x_lim = ax.get_xlim()
        self.y_lim = ax.get_ylim()


class GraphicManager:
    instance = None

    def __init__(self):
        GraphicManager.instance = self
        self.textures = {}

        width, height = pygame.display.get_window_size()
        self.main_texture = MainGraphTexture('main', width, height)
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

    def update_main(self):
        self.main_texture.update()