import imgui

from gui import global_var as g
from gui import components as imgui_c

print('logging subwindow loaded')
def show():
    if g.mLoggingWindowOpened:
        expanded, g.mLoggingWindowOpened = imgui.begin('日志窗口', True)
        g.mHoveringLoggingSubWindow = imgui_c.is_hovering_window()
        imgui.text('功能待实现')
        imgui.end()
