import pygame
from OpenGL.GL import *
import numpy as np


def create_texture_from_array(data):
    width, height, channels = data.shape

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

    width, height, channels = data.shape

    if channels == 3:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, data)
    elif channels == 4:
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, data)


class GraphicManager:
    instance = None

    def __init__(self):
        GraphicManager.instance = self
        self.width = None
        self.height = None
        self.texture_id = None
        self.update_size()

    def update_size(self):
        width, height = pygame.display.get_window_size()
        height -= 40
        self.width = width
        self.height = height
        data = np.random.randint(0, 256, (self.width, self.height, 4), dtype=np.uint8)
        self.texture_id = create_texture_from_array(data)

    def update(self):
        data = np.random.randint(0, 256, (self.width, self.height, 4), dtype=np.uint8)
        update_texture(self.texture_id, data)
