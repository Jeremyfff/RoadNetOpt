import imgui
import pygame

from gui import global_var as g
from gui import imgui_home_page
from gui import imgui_geo_page
from gui import imgui_training_page
from gui import imgui_tool_page
from gui import imgui_settings_page

print('main window loaded')
def show():
    screen_width, screen_height = g.mWindowSize
    imgui.set_next_window_size(g.LEFT_WINDOW_WIDTH, screen_height - g.BOTTOM_WINDOW_HEIGHT)
    imgui.set_next_window_position(0, 0)
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    expanded, opened = imgui.begin("main_window", False, flags=flags)
    imgui.push_id('main_window')
    if expanded:
        with imgui.begin_tab_bar('main_tab_bar'):
            if imgui.begin_tab_item('主页').selected:
                imgui_home_page.show()
                imgui.end_tab_item()
            if imgui.begin_tab_item('路网工具').selected:
                imgui_geo_page.show()
                imgui.end_tab_item()
            if imgui.begin_tab_item('训练工具').selected:
                imgui_training_page.show()
                imgui.end_tab_item()
            if imgui.begin_tab_item('实用工具').selected:
                imgui_tool_page.show()
                imgui.end_tab_item()
            if imgui.begin_tab_item('设置').selected:
                imgui_settings_page.show()
                imgui.end_tab_item()

        # end trees
    imgui.pop_id()
    imgui.end()
