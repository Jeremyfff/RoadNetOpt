from typing import Union
from typing import Union, TypeVar, Callable, Any

import matplotlib
import numpy as np
from OpenGL.GL import *
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import moderngl
import matplotlib.pyplot as plt
from moderngl_window.opengl.vao import VAO
from gui import global_var as g
import geopandas as gpd
from geo import Road, Building, Region
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _plot_gdf_func(**kwargs):
    assert 'gdf' in kwargs
    assert 'ax' in kwargs
    gdf = kwargs['gdf']
    kwargs.pop('gdf')

    if isinstance(gdf, gpd.GeoDataFrame):
        gdf.plot(**kwargs)
    elif isinstance(gdf, list):
        for df in gdf:
            df.plot(**kwargs)


def plot_as_array(gdf, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, tensor=True,
                  **kwargs):
    """kwargs 将会被传递给_plot_gdf_func的gdf.plot方法"""
    return plot_as_array2(_plot_gdf_func, width, height, y_lim, x_lim, transparent, antialiased, tensor, gdf=gdf,
                          **kwargs)


def plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False, tensor=True,
                   **kwargs):
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

    image_data: torch.Tensor = torch.frombuffer(canvas.buffer_rgba(), dtype=torch.uint8)
    image_data.to(device)
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
            new_image = torch.zeros((height, width, 4), dtype=torch.uint8)
            new_image[0:output_height, 0:output_width, :] = image_data
            image_data = new_image
    if not tensor:
        image_data = image_data.cpu().numpy()
    return image_data, ax


def world_space_to_image_space(world_x, world_y, x_lim, y_lim, image_width, image_height):
    assert x_lim[1] - x_lim[0] > 0
    assert y_lim[1] - y_lim[0] > 0

    image_x = int((world_x - x_lim[0]) / (x_lim[1] - x_lim[0]) * image_width)
    image_y = int((world_y - y_lim[0]) / (y_lim[1] - y_lim[0]) * image_height)
    image_y = image_height - image_y
    return image_x, image_y


def image_space_to_world_space(image_x, image_y, x_lim, y_lim, image_width, image_height):
    assert image_width != 0
    assert image_height != 0
    image_y = image_height - image_y
    world_x = (image_x / image_width) * (x_lim[1] - x_lim[0]) + x_lim[0]
    world_y = (image_y / image_height) * (y_lim[1] - y_lim[0]) + y_lim[0]

    return world_x, world_y


def create_texture_from_array_legacy(data):
    if isinstance(data, torch.Tensor):
        data = data.cpu().numpy()
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


def update_texture_legacy(texture_id, data):
    if isinstance(data, torch.Tensor):
        data = data.cpu().numpy()

    glBindTexture(GL_TEXTURE_2D, texture_id)
    height, width, channels = data.shape

    if channels == 3:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, data)
    elif channels == 4:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, data)


def create_texture_from_array(data):
    if isinstance(data, torch.Tensor):
        data = data.cpu().numpy()
    height, width, channels = data.shape
    texture = g.mCtx.texture((width, height), channels, data.tobytes())
    g.mModernglWindowRenderer.register_texture(texture)
    return texture.glo


def remove_texture(texture_id):
    assert texture_id in g.mModernglWindowRenderer._textures.keys()
    g.mModernglWindowRenderer.remove_texture(g.mModernglWindowRenderer._textures[texture_id])


def update_texture(texture_id, data):
    assert texture_id in g.mModernglWindowRenderer._textures.keys()
    texture: moderngl.Texture = g.mModernglWindowRenderer._textures[texture_id]
    texture.write(data.tobytes())


def blend_img_data(bot: torch.Tensor, top: torch.Tensor):
    # 分离 alpha 通道
    with torch.no_grad():
        bot_a = bot[:, :, 3] / 255.0
        top_a = top[:, :, 3] / 255.0

        bot_rgb = bot[:, :, :3].to(torch.float32)
        top_rgb = top[:, :, :3].to(torch.float32)
        # blended_rgb = (1 - top_a[:, :, np.newaxis]) * bot_rgb + top_a[:, :, np.newaxis] * top_rgb
        blended_rgb = (1 - top_a.unsqueeze(2)) * bot_rgb + top_a.unsqueeze(2) * top_rgb
        blended_alpha = bot_a + top_a * (1 - bot_a)
        blended_alpha = blended_alpha * 255
        blended = torch.cat((blended_rgb, blended_alpha.unsqueeze(2)), dim=2)
        blended = blended.to(torch.uint8)
        return blended


# region opengl
class GeoGL:
    def __init__(self, name, style_factory, vertices_data_get_func):
        self.name = name
        self.ctx = g.mCtx
        self.vao = VAO(name)
        self.style_factory = style_factory
        self.gdfs = None
        self.vertices_data_get_func = vertices_data_get_func

        self.buffer = None
        self.cached_vertices = None

        self.prog = g.mWindowEvent.load_program('programs/basic.glsl')
        self.prog['m_xlim'].value = (0, 1)
        self.prog['m_ylim'].value = (0, 1)

    def get_xy_lim(self):
        points = self.cached_vertices[:, :2]
        min_x = np.min(points[:, 0])
        max_x = np.max(points[:, 0])
        min_y = np.min(points[:, 1])
        max_y = np.max(points[:, 1])
        return (min_x, max_x), (min_y, max_y)

    def set_gdf(self, gdf):
        self.gdfs = gdf

    def set_style_factory(self, style_factory):
        self.style_factory = style_factory

    def update_buffer(self):
        if self.gdfs is None or len(self.gdfs) == 0:
            # self.cached_vertices = None
            # self.buffer = None
            print(f'{self.name} gdf is none, set cached vertices and buffer to None')
            return
        vertices = self.vertices_data_get_func(self.gdfs, self.style_factory)
        print(self.name)
        print(vertices)
        if self.buffer is None or len(vertices) != len(self.cached_vertices):
            print(f'{self.name} creating new buffer')
            self.vao._buffers = []
            self.vao.vaos = {}
            self.buffer = self.vao.buffer(vertices, '2f 4f', ['in_vert', 'in_color'])
        else:
            self.buffer.write(vertices)
            print(f'{self.name} use old buffer')
        self.cached_vertices = vertices

    def update_prog(self, x_lim: tuple, y_lim: tuple):
        self.prog['m_xlim'].value = np.array(x_lim, dtype=np.float32)
        self.prog['m_ylim'].value = np.array(y_lim, dtype=np.float32)

    def render(self):
        print(f'{self.name} rendering\n vertices is None?:{str(self.cached_vertices is None)}, gdfs is None?:{str(self.gdfs is None)}, buffer is None?:{str(self.buffer is None)}')
        if self.cached_vertices is None or self.gdfs is None or self.buffer is None:
            return

        self.vao.render(self.prog, mode=moderngl.TRIANGLES)


class RoadGL(GeoGL):
    def __init__(self, name, style_factory):
        super().__init__(name, style_factory, Road.get_vertices_data)


class BuildingGL(GeoGL):
    def __init__(self, name, style_factory):
        super().__init__(name, style_factory, Building.get_vertices_data)


class RegionGL(GeoGL):
    def __init__(self, name, style_factory):
        super().__init__(name, style_factory, Region.get_vertices_data)

class NodeGL(GeoGL):
    def __init__(self, name, style_factory):
        super().__init__(name, style_factory, Road.get_node_vertices_data)


# endregion
