import sys
import time
import imgui
import pygame
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl
import ctypes
import importlib

from graphic_module import GraphicManager

from gui.icon_module import IconManager
from gui import common
from gui import global_var as g
from gui import imgui_style

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


ctypes.windll.user32.SetProcessDPIAware()  # 禁用dpi缩放

"""
* Powered by DearImGui
* Online Manual - https://pthom.github.io/imgui_manual_online/manual/imgui_manual.html
"""


def imgui_debug_window():
    expanded, opened = imgui.begin('调试窗口', False)
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

    if imgui.tree_node('detail'):
        if imgui.button('reload main window'):
            importlib.reload(imgui_main_window)
        imgui.indent()
        if imgui.button('reload home page'):
            importlib.reload(imgui_home_page)
        if imgui.button('reload geo page'):
            importlib.reload(imgui_geo_page)
        if imgui.button('reload training page'):
            importlib.reload(imgui_training_page)
        if imgui.button('reload tool page'):
            importlib.reload(imgui_tool_page)
        if imgui.button('reload settings page'):
            importlib.reload(imgui_settings_page)
        imgui.unindent()
        if imgui.button('reload image window'):
            importlib.reload(imgui_image_window)
        imgui.indent()
        if imgui.button('reload main_texture_toolbox'):
            importlib.reload(imgui_main_texture_toolbox_subwindow)
        imgui.unindent()
        imgui.indent()
        if imgui.button('reload bottom window'):
            importlib.reload(imgui_bottom_window)
        if imgui.button('reload dxf sub window'):
            importlib.reload(imgui_dxf_subwindow)
        if imgui.button('reload info sub window'):
            importlib.reload(imgui_info_subwindow)
        if imgui.button('reload logging sub window'):
            importlib.reload(imgui_logging_subwindow)
        imgui.unindent()
        imgui.tree_pop()
    imgui.end()


def main():
    pygame.init()
    size = (g.INIT_WINDOW_WIDTH, g.INIT_WINDOW_HEIGHT)
    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
    pygame.display.set_caption('road net opt window')

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    imgui_style.init_font(impl)
    imgui_style.push_dark()

    graphic_manager = GraphicManager()
    icon_manager = IconManager()

    lst_time = time.time()
    while True:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            impl.process_event(event)
        impl.process_inputs()
        # update graphic

        common.update_main_graphic()

        # draw imgui windows
        imgui.new_frame()
        with imgui.font(g.mChineseFont):
            # put your windows here
            imgui_image_window.show()
            imgui_main_window.show()
            imgui_bottom_window.show()

            imgui_dxf_subwindow.show()
            imgui_info_subwindow.show()
            imgui_logging_subwindow.show()

            imgui_debug_window()

        g.mFrameTime = (time.time() - lst_time)
        lst_time = time.time()
        g.mFirstLoop = False

        # render and display
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()


if __name__ == "__main__":
    main()
