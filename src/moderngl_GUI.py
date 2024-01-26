import os
import sys
from PyQt5.QtWidgets import QSplashScreen, QApplication
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor
from PyQt5.QtCore import Qt
import ctypes

ctypes.windll.user32.SetProcessDPIAware()  # 禁用dpi缩放

"""
* Powered by DearImGui
* Online Manual - https://pthom.github.io/imgui_manual_online/manual/imgui_manual.html

* Wrapped by PyImgui
* https://pyimgui.readthedocs.io/en/latest/

* 使用ModernGL window渲染窗口图形
* https://github.com/moderngl/moderngl-window/
"""

# show splash
app = QApplication(sys.argv)
splash_pix = QPixmap('splash.png')
splash = QSplashScreen(splash_pix)
splash.show()


def show_splash_msg(msg):
    splash.showMessage(f"            Version 0.2 | 2024.01.25\n"
                       f"            Loading {msg}... \n\n",
                       Qt.AlignBottom, Qt.gray)
    app.processEvents()


show_splash_msg('py packages')
import importlib
import pyautogui
import imgui

show_splash_msg('Moderngl Window')
from moderngl_window.context.base import BaseKeys
import moderngl_window as mglw
from moderngl_window.integrations.imgui import ModernglWindowRenderer

show_splash_msg('Pytorch')
import torch

show_splash_msg('Geo Module')
from geo import road, building, region

show_splash_msg('Graphic Module')
import graphic_module

show_splash_msg('Icon Module')
from gui import icon_module

show_splash_msg('Gui Module')
from gui import common
from gui import global_var as g
from gui import imgui_style
from gui import components as imgui_c
from gui import imgui_bottom_window
from gui import imgui_dxf_subwindow
from gui import imgui_image_window
from gui import imgui_info_subwindow
from gui import imgui_logging_subwindow
from gui import imgui_debug_subwindow
from gui import imgui_main_texture_toolbox_subwindow
from gui import imgui_main_window
from gui import imgui_home_page
from gui import imgui_geo_page
from gui import imgui_training_page
from gui import imgui_tool_page
from gui import imgui_settings_page

show_splash_msg('DDPG')
from DDPG import env2 as env


def imgui_debug_subwindow_content():
    imgui.text('src')
    if imgui.button('reload graphic module'):
        importlib.reload(graphic_module)
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


imgui_debug_subwindow.set_debug_content(imgui_debug_subwindow_content)


class WindowEvents(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "路网织补工具 V0.2 (Powered by ModernGL)"
    aspect_ratio = None
    resource_dir = os.path.abspath(g.RESOURCE_DIR)
    vsync = True
    screen_width, screen_height = pyautogui.size()
    g.INIT_WINDOW_WIDTH = screen_width if g.INIT_WINDOW_WIDTH > screen_width else g.INIT_WINDOW_WIDTH
    g.INIT_WINDOW_HEIGHT = screen_height if g.INIT_WINDOW_HEIGHT > screen_height else g.INIT_WINDOW_HEIGHT
    window_size = (g.INIT_WINDOW_WIDTH, g.INIT_WINDOW_HEIGHT)
    keys = BaseKeys

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        _ = self.wnd.ctx.error
        self.imgui = ModernglWindowRenderer(self.wnd)

        self._exit_key = None
        self._fs_key = self.keys.F11

        # io = imgui.get_io()
        # io.display_size = size

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
        # update
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
            imgui_debug_subwindow.show()
        g.mFirstLoop = False

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def resize(self, width: int, height: int):
        self.imgui.resize(width, height)
        g.mWindowSize = self.wnd.size

    def key_event(self, key, action, modifiers):
        self.imgui.key_event(key, action, modifiers)
        common.handle_key_event(key, action, modifiers)

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


print(f'load complete')
# 关闭开屏画面
splash.finish(None)
mglw.run_window_config(WindowEvents)
