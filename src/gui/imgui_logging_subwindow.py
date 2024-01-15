import imgui

from gui import global_var as g
from gui import components as imgui_c

mHoveringLoggingSubWindow = False

print('logging subwindow loaded')
def show():
    global mHoveringLoggingSubWindow
    if g.mLoggingWindowOpened:
        expanded, g.mLoggingWindowOpened = imgui.begin('日志窗口', True)
        mHoveringLoggingSubWindow = imgui_c.is_hovering_window()
        imgui.text('功能待实现')
        imgui.end()
