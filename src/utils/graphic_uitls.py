
import matplotlib

from OpenGL.GL import *
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import matplotlib.pyplot as plt

from geopandas import GeoDataFrame

from utils.common_utils import timer

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


def plot_as_array(gdf, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False,tensor=True, **kwargs):
    """kwargs 将会被传递给_plot_gdf_func的gdf.plot方法"""
    return plot_as_array2(_plot_gdf_func, width, height, y_lim, x_lim, transparent, antialiased,tensor, gdf=gdf, **kwargs)



def plot_as_array2(plot_func, width, height, y_lim=None, x_lim=None, transparent=True, antialiased=False,tensor=True, **kwargs):
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


def create_texture_from_array(data):
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



def update_texture(texture_id, data):
    if isinstance(data, torch.Tensor):
        data = data.cpu().numpy()

    glBindTexture(GL_TEXTURE_2D, texture_id)
    height, width, channels = data.shape

    if channels == 3:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, data)
    elif channels == 4:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, data)



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
