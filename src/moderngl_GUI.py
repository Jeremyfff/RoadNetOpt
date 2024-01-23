import os
import sys
import time
import imgui
import numpy as np
from PIL import Image
from pathlib import Path
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl
import ctypes
import importlib
import pyautogui
from pyrr import Matrix44
import moderngl
import moderngl_window as mglw
from moderngl_window import geometry
from moderngl_window.integrations.imgui import ModernglWindowRenderer

import geo
from geo import road, building, region
import graphic_module

from gui import icon_module
from gui import common
from gui import global_var as g
from gui import imgui_style
from gui import components as imgui_c

from gui import imgui_bottom_window
from gui import imgui_dxf_subwindow
from gui import imgui_image_window
from gui import imgui_info_subwindow
from gui import imgui_logging_subwindow
from gui import imgui_main_texture_toolbox_subwindow
from gui import imgui_main_window
from gui import imgui_home_page
from gui import imgui_geo_page
from gui import imgui_training_page
from gui import imgui_tool_page
from gui import imgui_settings_page

from DDPG import env2 as env

ctypes.windll.user32.SetProcessDPIAware()  # 禁用dpi缩放

"""
* Powered by DearImGui
* Online Manual - https://pthom.github.io/imgui_manual_online/manual/imgui_manual.html

* Wrapped by PyImgui
* https://pyimgui.readthedocs.io/en/latest/

* 使用ModernGL渲染图形
* https://github.com/moderngl/moderngl-window/
"""


def imgui_debug_window():
    _, opened = imgui.begin('调试窗口', False)
    imgui.text('package gui')
    if imgui.button('reload all gui'):
        importlib.reload(imgui_home_page)
        importlib.reload(imgui_geo_page)
        importlib.reload(imgui_training_page)
        importlib.reload(imgui_tool_page)
        importlib.reload(imgui_settings_page)
        importlib.reload(imgui_main_window)

        importlib.reload(imgui_main_texture_toolbox_subwindow)
        importlib.reload(imgui_image_window)

        importlib.reload(imgui_dxf_subwindow)
        importlib.reload(imgui_info_subwindow)
        importlib.reload(imgui_logging_subwindow)
        importlib.reload(imgui_bottom_window)
    if imgui.button('reload common.py'):
        importlib.reload(common)
    if imgui.button('reload components.py'):
        importlib.reload(imgui_c)
    if imgui.button('reload imgui_style.py'):
        importlib.reload(imgui_style)
    if imgui.button('reload icon_module.py'):
        importlib.reload(icon_module)
    imgui.text('package geo')
    if imgui.button('reload road'):
        importlib.reload(road)
    if imgui.button('reload building'):
        importlib.reload(building)
    if imgui.button('reload region'):
        importlib.reload(region)
    imgui.text('package utils')
    imgui.text('package DDPG')
    if imgui.button('reload env'):
        importlib.reload(env)
    imgui.end()


class WindowEvents(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "路网织补工具 V0.2 (Powered by ModernGL)"
    aspect_ratio = None
    resource_dir = os.path.abspath(g.RESOURCE_DIR)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        # self.wnd.ctx.error
        self.imgui = ModernglWindowRenderer(self.wnd)

        screen_width, screen_height = self.wnd.size
        g.INIT_WINDOW_WIDTH = screen_width if g.INIT_WINDOW_WIDTH > screen_width else g.INIT_WINDOW_WIDTH
        g.INIT_WINDOW_HEIGHT = screen_height if g.INIT_WINDOW_HEIGHT > screen_height else g.INIT_WINDOW_HEIGHT
        size = (g.INIT_WINDOW_WIDTH, g.INIT_WINDOW_HEIGHT)

        io = imgui.get_io()
        io.display_size = size

        g.mWindowEvent = self
        g.mModernglWindowRenderer = self.imgui
        g.mCtx = self.ctx
        g.mWindowSize = self.wnd.size

        imgui_style.init_font(self.imgui)
        imgui_style.init_style_var()
        imgui_style.push_style(g.DARK_MODE)

        _ = graphic_module.GraphicManager()

    def render(self, _time: float, _frametime: float):
        g.mFrameTime = _frametime
        g.mTime = _time

        common.update_main_graphic()

        # Render UI to screen
        self.wnd.use()
        self.render_ui()

    def render_ui(self):
        """Render the UI"""
        # draw imgui windows
        imgui.new_frame()
        with imgui.font(g.mChineseFont):
            imgui_image_window.show()
            imgui_main_window.show()
            imgui_bottom_window.show()

            imgui_dxf_subwindow.show()
            imgui_info_subwindow.show()
            imgui_logging_subwindow.show()

            imgui_debug_window()

        g.mFirstLoop = False

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def resize(self, width: int, height: int):
        self.imgui.resize(width, height)
        g.mWindowSize = self.wnd.size

    def key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.imgui.mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)


if __name__ == '__main__':
    mglw.run_window_config(WindowEvents)
