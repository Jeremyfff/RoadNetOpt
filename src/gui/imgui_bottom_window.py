import imgui
import pygame
from gui import global_var as g
from gui import global_info as gi
from gui import components as imgui_c


print('bottom window loaded')
def show():
    screen_width, screen_height = g.mWindowSize
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.set_next_window_size(screen_width, g.BOTTOM_WINDOW_HEIGHT)
    imgui.set_next_window_position(0, screen_height - g.BOTTOM_WINDOW_HEIGHT)

    imgui.begin("bottom window", False, flags=flags)
    imgui.text(f'{gi.LAST_MODIFIED} V{gi.RELEASE_VERSION}')
    imgui.same_line()
    if imgui.button('信息窗口'):
        g.mInfoWindowOpened = True
    imgui.same_line()
    if imgui.button('输出窗口'):
        g.mLoggingWindowOpened = True
    imgui.same_line()
    if imgui.button('调试窗口'):
        g.mDebugWindowOpened = True
    imgui.end()
